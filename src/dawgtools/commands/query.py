"""Execute an sql query.

Renders a jinja2 query template string into a parameterized sql query.

For example:

  $ dawgtools -v query -q "select 'foo' as col1, {{ barval }} as col2" -p barval=bar
  {"col1": "foo", "col2": "bar"}
"""

import argparse
import csv
import gzip
from subprocess import run, CalledProcessError
import tempfile
import logging
import json

from jinja2 import Template

from dawgtools.utils import StdOut
from dawgtools import db

log = logging.getLogger(__name__)


def build_parser(parser):
    parser.add_argument('-q', '--query', help="sql command")
    parser.add_argument('-i', '--infile', type=argparse.FileType('r'),
                        help="Input file containing an sql command")
    parser.add_argument('-p', '--params', nargs='*',
                        help="""One or more variable value pairs in
                        the form -e var=val; these are used as
                        parameters when rendering the query.""")
    parser.add_argument('-o', '--outfile',
                        help="""Output file name; uses gzip compression
                        if ends with .gz or stdout if not provided.""")
    parser.add_argument('-f', '--format', default='lines',
                        choices=['lines', 'dicts', 'lists'],
                        help='Output format [%(default)s]')
    parser.add_argument('-n', '--dry-run', action='store_true', default=False,
                        help='Print the rendered query and exit')


def action(args):

    if args.params:
        params = dict([var.split('=') for var in args.params])
    else:
        params = {}

    if args.query:
        query = args.query
    elif args.infile:
        query = args.infile.read()
    else:
        raise ValueError("Must provide either a query or an input file")

    if args.dry_run:
        sql, params = db.render_template(query, params)
        print(sql)
        print(f"Parameters: {params}")
        return

    headers, rows = db.sql_query(query, params)

    if args.outfile:
        outfile = args.outfile.format(**params)
        if outfile.endswith('.gz'):
            opener = gzip.open
        else:
            opener = open
    else:
        outfile = None
        opener = StdOut

    with opener(outfile, 'wt', encoding='utf-8', errors='ignore') as f:
        if args.format == 'lines':
            for row in db.as_dicts(headers, rows):
                f.write(json.dumps(row) + '\n')
        elif args.format == 'dicts':
            f.write(json.dumps(db.as_dicts(headers, rows), indent=2))
        elif args.format == 'lists':
            f.write(json.dumps(dict(
                fieldnames=headers,
                data=[list(row) for row in rows],
            ), indent=2))
