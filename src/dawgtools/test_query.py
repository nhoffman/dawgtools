import pytest

from dawgtools import db
from dawgtools.main import parse_arguments


@pytest.mark.parametrize(
    'argv, headers, rows, expected_sql, expected_params, expected_output',
    [
        (
            ['query', '-q', 'select 1 as col1, 2 as col2', '-f', 'csv'],
            ['col1', 'col2'], [[1, 2]],
            'select 1 as col1, 2 as col2', [],
            'col1,col2\n1,2\n',
        ),
        (
            ['-v', 'query', '-q', "select 'foo' as col1, %(barval)s as col2",
             '-p', 'barval=bar'],
            ['col1', 'col2'], [['foo', 'bar']],
            "select 'foo' as col1, ? as col2", ['bar'],
            '{"col1": "foo", "col2": "bar"}\n',
        ),
    ],
)
def test_documented_queries_without_temp_table(
    argv, headers, rows, expected_sql, expected_params, expected_output,
    monkeypatch, capsys,
):
    def fake_sql_query(query, params, callback=None):
        assert callback is None
        assert db.render_template(query, params) == (expected_sql, expected_params)
        return headers, rows

    monkeypatch.setattr(db, 'sql_query', fake_sql_query)
    action, args = parse_arguments(argv)
    action(args)

    assert capsys.readouterr().out.replace('\r\n', '\n') == expected_output


def test_documented_query_with_mrns(tmp_path, monkeypatch, capsys):
    mrns = tmp_path / 'mrns.txt'
    mrns.write_text('fee\nfie\nfo\nfum\n')
    rows = [[mrn] for mrn in ['fee', 'fie', 'fo', 'fum']]
    cursor = object()
    loaded = []

    def fake_load_table(cursor, sql_cmd, rows):
        loaded.append((cursor, sql_cmd, rows))

    def fake_sql_query(query, params, callback=None):
        assert db.render_template(query, params) == ('select * from #mrns', [])
        callback(cursor=cursor)
        return ['mrn'], rows

    monkeypatch.setattr(db, 'create_and_load_temp_table', fake_load_table)
    monkeypatch.setattr(db, 'sql_query', fake_sql_query)
    action, args = parse_arguments([
        'query', '--mrns', str(mrns), '-q', 'select * from #mrns',
    ])
    try:
        action(args)
    finally:
        args.mrns.close()

    assert loaded == [(
        cursor,
        'drop table if exists #mrns; create table #mrns (mrn varchar(102));',
        [{'mrn': row[0]} for row in rows],
    )]
    assert capsys.readouterr().out == ''.join(
        f'{{"mrn": "{row[0]}"}}\n' for row in rows
    )
