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


def build_parser(parser):
    parser.add_argument('schema', help="json file with feature schema")
    parser.add_argument('-i', '--infile', help="A single input file")
    parser.add_argument('-d', '--dirname', help="A directory of input files")
    parser.add_argument('-p', '--prompt', type=argparse.FileType('r'),
                        help="Optional file with additional prompt content",)
    parser.add_argument('-o', '--outfile', help="Output file",
                        default=sys.stdout, type=argparse.FileType('w'))
    parser.add_argument('-m', '--model', help="Model name [%(default)s]", default='gpt-5.2')
    parser.add_argument('--cache-dir', default="extract_batch_cache",
                        help="Directory containing cached results [%(default)s]")
    parser.add_argument('-n', '--no-cache', dest='use_cache', action='store_false', default=True)


def action(args):

    schema_file = Path(args.schema)
    schema_contents = schema_file.read_text()
    schema_hash = hashlib.md5(schema_contents.encode('utf-8')).hexdigest()
    cache_dir = Path(args.cache_dir) / f'{schema_file.stem}-{schema_hash}'

    if args.use_cache:
        Path(cache_dir).mkdir(parents=True, exist_ok=True)

    if not (args.infile or args.dirname):
        exit('Either -i/--infile or -d/--dirname must be specified')

    if args.prompt:
        prompt = args.prompt.read()
    else:
        prompt = None

    files = [Path(args.infile)] if args.infile else []
    if args.dirname:
        files.extend(
            p for p in Path(args.dirname).iterdir()
            if p.is_file() and p.suffix.lower() in {'.txt', '.md'}
        )

    client = OpenAI()

    schema = json.loads(schema_contents)

    fieldnames = ['filename', 'model'] + list(schema['parameters']['properties'].keys())
    writer = csv.DictWriter(args.outfile, fieldnames=fieldnames, extrasaction='ignore')
    writer.writeheader()

    for infile in sorted(files):
        cache_file = cache_dir / f'{infile.stem}-{args.model}.json'
        if args.use_cache and cache_file.exists():
            print(f'Loading cached results for {infile}...', file=sys.stderr)
            features = json.loads(cache_file.read_text())
        else:
            print(f'Processing {infile}...', file=sys.stderr)
            response = get_features(
                client=client,
                content=infile.read_text(),
                tools=[schema],
                model=args.model,
                prompt=prompt,
            )
            features = response.to_dict()
            if args.use_cache:
                cache_file.write_text(response.to_json())

        for i, feature in enumerate(feature_table(features), 1):
            tab = {'filename': infile.name, 'model': args.model}
            tab.update({k: '' for k in fieldnames[2:]})  # ensure all fields present
            tab.update(feature)
            writer.writerow(tab)
