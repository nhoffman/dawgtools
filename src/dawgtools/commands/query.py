"""Execute an sql query.

Renders a query template string into a parameterized sql query.

Use a combination of python string formatting directives (for variable
substituion) and jinja2 expressions (for conditional expressions).

For example:

  $ dawgtools -v query -q "select 'foo' as col1, %(barval)s as col2" -p barval=bar
  {"col1": "foo", "col2": "bar"}

"""

import argparse
import csv
import gzip
import json
import logging

from dawgtools import db
from dawgtools.utils import MyJSONEncoder, StdOut

log = logging.getLogger(__name__)


def create_and_load_temp_table(sql_cmd: str, fobj: argparse.FileType):
    """Create and load a temporary table using the provided schema
    and data files.
    """

    log.info("Creating temporary table")
    db.sql_command(sql_cmd)

    log.info("Loading data into temporary table")
    reader = csv.reader(fobj)
    headers = next(reader)
    placeholders = ','.join(['?'] * len(headers))
    insert_sql = f"insert into temp_table ({', '.join(headers)}) values ({placeholders})"
    with db.get_connection().cursor() as cur:
        for row in reader:
            cur.execute(insert_sql, row)
        db.get_connection().commit()


def build_parser(parser):

    inputs = parser.add_argument_group('inputs')
    inputs.add_argument('-q', '--query', help="sql command")
    inputs.add_argument('-i', '--infile', type=argparse.FileType('r'),
                        help="Input file containing an sql command")
    inputs.add_argument('-n', '--query-name', choices=db.list_queries(),
                        help="name of an sql query")
    inputs.add_argument('-p', '--params', nargs='*',
                        help="""One or more variable value pairs in
                        the form -e var=val; these are used as
                        parameters when rendering the query.""")
    inputs.add_argument('-P', '--params-file',
                        help="""json file containing parameter values""")

    temptable = parser.add_argument_group('temptable')
    temptable.add_argument('--temp-schema', metavar='FILE', type=argparse.FileType('r'),
                           help="""File containing schema for a temporary
                           table to be created before running the query.""")
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
    outputs.add_argument('-f', '--format', default='lines',
                         choices=['lines', 'dicts', 'lists'],
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
                f.write(json.dumps(row, cls=MyJSONEncoder) + '\n')
        elif args.format == 'dicts':
            f.write(json.dumps(db.as_dicts(headers, rows), indent=2, cls=MyJSONEncoder))
        elif args.format == 'lists':
            f.write(json.dumps(dict(
                fieldnames=headers,
                data=[list(row) for row in rows],
            ), indent=2, cls=MyJSONEncoder))
