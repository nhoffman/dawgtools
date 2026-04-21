"""Extract features from one or more input files.

Environment
-----------

- ``OPENAI_API_KEY`` must be set.
- ``OPENAI_BASE_URL`` can be used to set a custom API base URL.

Set environment variables::

  export OPENAI_API_KEY="sk-..."
  export OPENAI_BASE_URL="https://api.openai.com/v1"  # optional

Example
-------

Given a schema file (e.g., developed using toolbuilder) and a directory of text
files named ``input_texts``, extract features into ``features.csv``::

  dawgtools extract_batch schema.json -d input_texts -o features.csv

Caching
-------

A cache directory is created to store intermediate results and avoid re-querying
the model for files that have already been processed. New model queries are
performed each time the schema file changes.

Schema format
-------------

The schema file should be a JSON file defining a tool compatible with the OpenAI
function calling API. See:

https://platform.openai.com/docs/guides/function-calling

Example schema (from the OpenAI documentation):

.. code-block:: json

   {
     "type": "function",
     "name": "extract_features",
     "description": "Extract features from text",
     "parameters": {
       "type": "object",
       "properties": {
         "feature1": {
           "type": "string",
           "description": "Description of feature1"
         },
         "feature2": {
           "type": "integer",
           "description": "Description of feature2"
         }
       },
       "required": ["feature1", "feature2"]
     }
   }

"""

import argparse
import sys
import json
from pathlib import Path
import csv
import hashlib
from itertools import islice

from openai import OpenAI


def get_features(client: OpenAI,
                 content: str,
                 tools: list,
                 model: str,
                 prompt: str = None,
                 **kwargs) -> dict:

    messages = [{'role': 'user', 'content': content}]

    if prompt:
        messages.append({'role': 'user', 'content': prompt})

    response = client.responses.create(
        model=model,
        input=messages,
        tools=tools,
        tool_choice='required',
        **kwargs
    )

    return response


def feature_table(response: dict) -> list[dict]:
    output = (o for o in response['output'] if 'arguments' in o)
    return [json.loads(o['arguments']) for o in output]


def unique(items: list[str]) -> list[str]:
    return list(dict.fromkeys(items))


def build_cache_key(cache_basis: str, model: str) -> str:
    digest = hashlib.md5(f'{model}\0{cache_basis}'.encode('utf-8')).hexdigest()
    return f'item-{digest}'


def response_to_dict(response) -> dict:
    if hasattr(response, 'to_dict'):
        return response.to_dict()
    return response


def response_to_json(response, response_dict: dict) -> str:
    if hasattr(response, 'to_json'):
        return response.to_json()
    return json.dumps(response_dict)


def validate_args(args) -> None:
    if args.datafile:
        if not args.data_cols:
            exit('--data-cols is required when --datafile is provided')
        return

    if args.include_cols is not None or args.data_cols is not None:
        exit('--include-cols and --data-cols require --datafile')

    if not (args.infile or args.dirname):
        exit('Either -i/--infile, -d/--dirname, or -f/--datafile must be specified')


def build_fieldnames(args, schema: dict) -> list[str]:
    feature_names = list(schema['parameters']['properties'].keys())
    if args.datafile:
        include_cols = args.include_cols or []
        return unique(include_cols + ['model'] + feature_names)
    return unique(['filename', 'model'] + feature_names)


def iter_file_inputs(args):
    files = [Path(args.infile)] if args.infile else []
    if args.dirname:
        files.extend(
            p for p in Path(args.dirname).iterdir()
            if p.is_file() and p.suffix.lower() in {'.txt', '.md'}
        )

    for infile in sorted(files):
        yield dict(
            label=str(infile),
            cache_basis=infile.stem,
            row_data={'filename': infile.name},
            content=infile.read_text(),
        )


def iter_csv_inputs(args):
    include_cols = args.include_cols or []
    required_cols = unique(include_cols + args.data_cols)

    with open(args.datafile, newline='', encoding='utf-8', errors='ignore') as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError(f'CSV file has no header row: {args.datafile}')

        missing = [col for col in required_cols if col not in reader.fieldnames]
        if missing:
            cols = ', '.join(missing)
            raise ValueError(f'Missing CSV columns in {args.datafile}: {cols}')

        for rownum, row in enumerate(reader, 1):
            parts = [
                str(row[col]).strip()
                for col in args.data_cols
                if row.get(col) not in {None, ''}
            ]
            content = '\n'.join(part for part in parts if part)
            yield dict(
                label=f'{args.datafile} row {rownum}',
                cache_basis=content,
                row_data={col: row.get(col, '') for col in include_cols},
                content=content,
            )


def limit_inputs(records, max_items):
    if max_items is None:
        return records
    return islice(records, max_items)


def build_parser(parser):
    parser.add_argument('schema', help="json file with feature schema")
    inputs = parser.add_argument_group('input')
    inputs.add_argument('-i', '--infile', help="A single input file")
    inputs.add_argument('-d', '--dirname', help="A directory of input files")
    inputs.add_argument('-f', '--datafile', help="CSV file containing input rows")
    inputs.add_argument('--include-cols', nargs='*',
                        help="CSV columns to include in the output when using --datafile")
    inputs.add_argument('--data-cols', nargs='+',
                        help="CSV columns whose contents are concatenated and sent to the model")
    parser.add_argument('-p', '--prompt', type=argparse.FileType('r'),
                        help="Optional file with additional prompt content",)
    parser.add_argument('-o', '--outfile', help="Output file",
                        default=sys.stdout, type=argparse.FileType('w'))
    parser.add_argument('-m', '--max-items', type=int,
                        help="Maximum number of inputs to process")
    parser.add_argument('--model', help="Model name [%(default)s]", default='gpt-5.4')
    parser.add_argument('--cache-dir', default="extract_batch_cache",
                        help="Directory containing cached results [%(default)s]")
    parser.add_argument('-n', '--no-cache', dest='use_cache', action='store_false', default=True)


def action(args):
    validate_args(args)

    schema_file = Path(args.schema)
    schema_contents = schema_file.read_text()
    schema_hash = hashlib.md5(schema_contents.encode('utf-8')).hexdigest()
    cache_dir = Path(args.cache_dir) / f'{schema_file.stem}-{schema_hash}'

    if args.use_cache:
        Path(cache_dir).mkdir(parents=True, exist_ok=True)

    if args.prompt:
        prompt = args.prompt.read()
    else:
        prompt = None

    client = OpenAI()
    schema = json.loads(schema_contents)
    fieldnames = build_fieldnames(args, schema)
    writer = csv.DictWriter(args.outfile, fieldnames=fieldnames, extrasaction='ignore')
    writer.writeheader()

    if args.datafile:
        records = iter_csv_inputs(args)
    else:
        records = iter_file_inputs(args)

    for record in limit_inputs(records, args.max_items):
        cache_key = build_cache_key(record['cache_basis'], args.model)
        cache_file = cache_dir / f'{cache_key}.json'
        if args.use_cache and cache_file.exists():
            print(f'Loading cached results for {record["label"]}...', file=sys.stderr)
            features = json.loads(cache_file.read_text())
        else:
            print(f'Processing {record["label"]}...', file=sys.stderr)
            response = get_features(
                client=client,
                content=record['content'],
                tools=[schema],
                model=args.model,
                prompt=prompt,
            )
            features = response_to_dict(response)
            if args.use_cache:
                cache_file.write_text(response_to_json(response, features))

        for feature in feature_table(features):
            tab = {k: '' for k in fieldnames}
            tab.update(record['row_data'])
            tab['model'] = args.model
            tab.update(feature)
            writer.writerow(tab)
