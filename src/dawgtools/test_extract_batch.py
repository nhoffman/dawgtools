import argparse
import csv
import json

import pytest

from dawgtools.commands import extract_batch


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def to_dict(self):
        return self.payload

    def to_json(self):
        return json.dumps(self.payload)


def make_parser():
    parser = argparse.ArgumentParser()
    extract_batch.build_parser(parser)
    return parser


def write_schema(path):
    path.write_text(json.dumps({
        'type': 'function',
        'name': 'extract_features',
        'description': 'Extract features from text',
        'parameters': {
            'type': 'object',
            'properties': {
                'feature': {'type': 'string'},
            },
            'required': ['feature'],
        },
    }))


def test_datafile_requires_data_cols(tmp_path):
    schema = tmp_path / 'schema.json'
    datafile = tmp_path / 'input.csv'
    outfile = tmp_path / 'out.csv'

    write_schema(schema)
    datafile.write_text('keep,text\nrow,content\n')

    parser = make_parser()
    args = parser.parse_args([str(schema), '-f', str(datafile), '-o', str(outfile), '-n'])

    with pytest.raises(SystemExit) as excinfo:
        extract_batch.action(args)

    assert excinfo.value.code == '--data-cols is required when --datafile is provided'
    args.outfile.close()


def test_cache_key_includes_model_name():
    key1 = extract_batch.build_cache_key('same-input', 'gpt-5.2')
    key2 = extract_batch.build_cache_key('same-input', 'gpt-5.4')

    assert key1 != key2


def test_datafile_ignores_infile_and_dirname_and_uses_include_cols(tmp_path, monkeypatch):
    schema = tmp_path / 'schema.json'
    datafile = tmp_path / 'input.csv'
    infile = tmp_path / 'input.txt'
    indir = tmp_path / 'inputs'
    outfile = tmp_path / 'out.csv'

    write_schema(schema)
    datafile.write_text('mrn,note,addendum\n1,alpha,beta\n2,gamma,delta\n')
    infile.write_text('this should be ignored')
    indir.mkdir()
    (indir / 'ignored.txt').write_text('ignore me too')

    seen = []

    def fake_get_features(client, content, tools, model, prompt=None, **kwargs):
        seen.append(content)
        return FakeResponse({
            'output': [
                {'arguments': json.dumps({'feature': f'extracted:{content}'})},
            ]
        })

    monkeypatch.setattr(extract_batch, 'OpenAI', lambda: object())
    monkeypatch.setattr(extract_batch, 'get_features', fake_get_features)

    parser = make_parser()
    args = parser.parse_args([
        str(schema),
        '-i', str(infile),
        '-d', str(indir),
        '-f', str(datafile),
        '--include-cols', 'mrn',
        '--data-cols', 'note', 'addendum',
        '-o', str(outfile),
        '-n',
    ])

    extract_batch.action(args)
    args.outfile.close()

    assert seen == ['alpha\nbeta', 'gamma\ndelta']
    expected_model = args.model

    with outfile.open(newline='') as handle:
        rows = list(csv.DictReader(handle))

    assert rows == [
        {'mrn': '1', 'model': expected_model, 'feature': 'extracted:alpha\nbeta'},
        {'mrn': '2', 'model': expected_model, 'feature': 'extracted:gamma\ndelta'},
    ]
    assert 'filename' not in rows[0]


def test_file_mode_keeps_filename_column(tmp_path, monkeypatch):
    schema = tmp_path / 'schema.json'
    infile = tmp_path / 'input.txt'
    outfile = tmp_path / 'out.csv'

    write_schema(schema)
    infile.write_text('hello world')

    def fake_get_features(client, content, tools, model, prompt=None, **kwargs):
        return FakeResponse({
            'output': [
                {'arguments': json.dumps({'feature': 'ok'})},
            ]
        })

    monkeypatch.setattr(extract_batch, 'OpenAI', lambda: object())
    monkeypatch.setattr(extract_batch, 'get_features', fake_get_features)

    parser = make_parser()
    args = parser.parse_args([
        str(schema),
        '-i', str(infile),
        '-o', str(outfile),
        '-n',
    ])

    extract_batch.action(args)
    args.outfile.close()
    expected_model = args.model

    with outfile.open(newline='') as handle:
        rows = list(csv.DictReader(handle))

    assert rows == [
        {'filename': 'input.txt', 'model': expected_model, 'feature': 'ok'},
    ]


def test_max_items_limits_csv_inputs(tmp_path, monkeypatch):
    schema = tmp_path / 'schema.json'
    datafile = tmp_path / 'input.csv'
    outfile = tmp_path / 'out.csv'

    write_schema(schema)
    datafile.write_text('mrn,note\n1,alpha\n2,beta\n3,gamma\n')

    seen = []

    def fake_get_features(client, content, tools, model, prompt=None, **kwargs):
        seen.append(content)
        return FakeResponse({
            'output': [
                {'arguments': json.dumps({'feature': content.upper()})},
            ]
        })

    monkeypatch.setattr(extract_batch, 'OpenAI', lambda: object())
    monkeypatch.setattr(extract_batch, 'get_features', fake_get_features)

    parser = make_parser()
    args = parser.parse_args([
        str(schema),
        '-f', str(datafile),
        '--include-cols', 'mrn',
        '--data-cols', 'note',
        '-m', '2',
        '-o', str(outfile),
        '-n',
    ])

    extract_batch.action(args)
    args.outfile.close()

    assert seen == ['alpha', 'beta']
    expected_model = args.model

    with outfile.open(newline='') as handle:
        rows = list(csv.DictReader(handle))

    assert rows == [
        {'mrn': '1', 'model': expected_model, 'feature': 'ALPHA'},
        {'mrn': '2', 'model': expected_model, 'feature': 'BETA'},
    ]
