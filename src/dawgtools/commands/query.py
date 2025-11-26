"""Execute an sql query.

Renders a query template string into a parameterized sql query.

Use a combination of python string formatting directives (for variable
substituion) and jinja2 expressions (for conditional expressions).

For example:

  $ dawgtools -v query -q "select 'foo' as col1, %(barval)s as col2" -p barval=bar
  {"col1": "foo", "col2": "bar"}

The command may be preceded by the creation and loading of a temporary table
containing mrns that can be referenced in the query. For example:

  $ cat mrns.txt
  fee
  fie
  fo
  fum
  $ dawgtools query --mrns mrns.txt -q 'select * from #mrns'
  {"mrn": "fee"}
  {"mrn": "fie"}
  {"mrn": "fo"}
  {"mrn": "fum"}
"""

import argparse
import csv
import gzip
import json
import logging
import sys
from functools import partial

from dawgtools import db
from dawgtools.utils import MyJSONEncoder, StdOut

log = logging.getLogger(__name__)

# Increase CSV field size limit to maximim possible
# https://stackoverflow.com/a/15063941
# avoids "_csv.Error: field larger than field limit (131072)"
field_size_limit = sys.maxsize

while True:
    try:
        csv.field_size_limit(field_size_limit)
        break
    except OverflowError:
        field_size_limit = int(field_size_limit / 10)


def build_parser(parser):

    inputs = parser.add_argument_group('inputs')
    inputs.add_argument('-q', '--query', help="sql command")
    inputs.add_argument('-i', '--infile', type=argparse.FileType('r'),
                        help="Input file containing an sql command")
    inputs.add_argument('-n', '--query-name', choices=db.list_queries(),
                        help="name of an sql query")
    inputs.add_argument('-p', '--params', nargs='*',
                        help="""One or more variable value pairs in
                        the form -p var=val; these are used as
                        parameters when rendering the query.""")
    inputs.add_argument('-P', '--params-file',
                        help="""json file containing parameter values""")

    temptable = parser.add_argument_group('temptable')
    temptable.add_argument('--mrns', metavar='FILE', type=argparse.FileType('r'),
                           help="""A file containing
                           whitespace-delimited mrns to be loaded into
                           a temporary table '#mrns(mrn varchar(102))'
                           before the query.""")
    temptable.add_argument('--temp-schema', metavar='FILE', type=argparse.FileType('r'),
                           help="""File containing schema for a
                           temporary table to be created before
                           running the query.""")
    temptable.add_argument('--temp-data', metavar='FILE', type=argparse.FileType('r'),
                           help="""CSV file with columns corresponding
                           to the schema containing data to load into
                           the temporary table before running the
                           query. Requires --temp-schema. Columns not
                           in the schema are ignored.""")

    outputs = parser.add_argument_group('outputs')
    outputs.add_argument('-o', '--outfile',
                         help="""Output file name; uses gzip compression
                         if ends with .gz or stdout if not provided.""")
    outputs.add_argument('-f', '--format', default='jsonl',
                         choices=['jsonl', 'json', 'json-rows', 'csv'],
                         help='Output format [%(default)s]')

    parser.add_argument('-x', '--dry-run', action='store_true', default=False,
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
    elif args.query_name:
        query = db.get_query(args.query_name)
    else:
        raise ValueError("Must provide either a query, input file, or query name")

    if args.dry_run:
        sql, params = db.render_template(query, params)
        print(sql)
        print(f"Parameters: {params}")
        return

    if args.temp_schema and args.temp_data:
        callback = partial(
            db.create_and_load_temp_table,
            sql_cmd=args.temp_schema.read(),
            rows=list(csv.DictReader(args.temp_data))
        )
    elif args.mrns:
        callback = partial(
            db.create_and_load_temp_table,
            sql_cmd='drop table if exists #mrns; create table #mrns (mrn varchar(102));',
            rows=[{'mrn': mrn} for mrn in args.mrns.read().split()]
        )

    headers, rows = db.sql_query(query, params, callback=callback)

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
        if args.format == 'jsonl':
            for row in db.as_dicts(headers, rows):
                f.write(json.dumps(row, cls=MyJSONEncoder) + '\n')
        elif args.format == 'json':
            f.write(json.dumps(db.as_dicts(headers, rows), indent=2, cls=MyJSONEncoder))
        elif args.format == 'json-rows':
            f.write(json.dumps(dict(
                fieldnames=headers,
                data=[list(row) for row in rows],
            ), indent=2, cls=MyJSONEncoder))
        elif args.format == 'csv':
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(rows)
