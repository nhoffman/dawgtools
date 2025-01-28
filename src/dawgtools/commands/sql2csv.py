"""Reformat sqlcmd output to csv in am-dawg-tool environment

- writes output of the sql query to a temporary file
- saves query as unicode and converts utf-16 to utf-8
- replaces "NULL" with empty cells
- drops rows with a length that differs from the header row

The input file may contain variable placeholders using curly braces -
these will be substituted for values provided using -e/--environment.
The same variables will be substituted in the output file name. For
example:

$ cat test.sql
select
1 as col1
,cast('{date}' as date) as col2

$ sql2csv.py test.sql -o 'test-{date}.csv' -p -e date=2023-03-01
select
1 as col1
,cast('2023-03-01' as date) as col2

$ ls test*
test.sql  test-2023-03-01.csv

$ cat test-2023-03-01.csv
col1,col2
1,2023-03-01
"""

import os
import sys
import argparse
import csv
import gzip
from subprocess import run, CalledProcessError
import tempfile
import logging

log = logging.getLogger(__name__)


class StdOut:
    def __init__(self, *args, **kwargs):
        pass

    def __enter__(self):
        self.fobj = sys.stdout
        return self.fobj

    def __exit__(self, exc_type, exc_value, traceback):
        pass


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


def nonull(row, maxchars=1000):
    """Replace NULL with '' and limit other values to maxchars characters."""
    return ['' if x == 'NULL' else x[:maxchars] for x in row]


def build_parser(parser):
    parser.add_argument('infile', help="Input file containing an sql command")
    parser.add_argument('-o', '--outfile',
                        help="""Output file name; uses gzip compression
                        if ends with .gz or stdout if not provided.""")
    parser.add_argument('-p', '--print-query', action='store_true', default=False,
                        help='Print the query to stdout before executing')
    parser.add_argument('-n', '--dry-run', action='store_true', default=False,
                        help='Read the query file and exit')
    parser.add_argument('-e', '--environment', nargs='*',
                        help="""One or more variable value pairs in
                        the form -e var=val; these are used as format
                        string arguments when rendering the query.""")


def action(args):
    tempoutfile, tempout = tempfile.mkstemp()
    os.close(tempoutfile)

    if args.environment:
        environment = dict([var.split('=') for var in args.environment])
    else:
        environment = {}

    with (open(args.infile, encoding='utf-8') as sqlfile,
          tempfile.NamedTemporaryFile('w', delete=False) as sqltemp):
        query_text = sqlfile.read().format(**environment)

        if args.print_query:
            print(query_text)

        if args.dry_run:
            return

        sqltemp.write('SET NOCOUNT ON;\n\n')
        sqltemp.write(query_text)

    try:
        # https://learn.microsoft.com/en-us/sql/tools/sqlcmd-utility?view=sql-server-ver16
        cmd = [
            'sqlcmd',
            '-S', 'am-dawg-sql-trt',
            '-i', sqltemp.name,
            '-o', tempout,
            '-s', '|',
            '-k', '2',
            '-E',
            '-W',
            '-m1',
            '-b',
            '-u',
        ]

        run(cmd, check=True)

        if args.outfile:
            outfile = args.outfile.format(**environment)
            if outfile.endswith('.gz'):
                opener = gzip.open
            else:
                opener = open
        else:
            outfile = None
            opener = StdOut

        with (open(tempout, 'r', encoding='utf-16') as tempin,
              opener(outfile, 'wt', encoding='utf-8', errors='ignore') as f):
            reader = csv.reader(tempin, delimiter='|')
            headers = next(reader)
            rowlen = len(headers)
            next(reader)  # second row is just dashes
            writer = csv.writer(f, dialect='unix', quoting=csv.QUOTE_MINIMAL)
            writer.writerow(headers)
            writer.writerows((nonull(row) for row in reader if len(row) == rowlen))

    except CalledProcessError as err:
        print(err)
        run(['cat', tempout], check=True)
    except Exception as err:
        print(err)
    finally:
        os.remove(tempout)
        os.remove(sqltemp.name)

