import json
import logging
import re
from operator import itemgetter
from pathlib import Path
from types import FunctionType

import pyodbc
from jinja2 import Template

log = logging.getLogger(__name__)


CONNECTION_STRING = ';'.join([
    'DRIVER={ODBC Driver 17 for SQL Server}',
    'SERVER=am-dawg-sql-trt',
    'Trusted_Connection=yes'
])


def list_queries() -> list[str]:
    names = (Path(__file__).parent / 'queries').glob('*.sql')
    return [name.stem for name in names]


def get_query(name: str) -> str:
    query_file = Path(__file__).parent / 'queries' / f'{name}.sql'
    with open(query_file, encoding='utf-8') as f:
        return f.read()


def render_template(template: str, params: dict) -> tuple[str, list]:
    """Renders a query template that uses a combination of python
    string formatting directives and jinja2 expressions using the
    given parameters. Returns a tuple of the modified template with
    "?" placeholders and a list of positional parameters.

    """

    rendered = Template(template).render(params)

    # Find all string formatting directives in the rendered output and create a list of values
    format_directive_pattern = re.compile(r'%\((.*?)\)s')
    keys = format_directive_pattern.findall(rendered)
    positional_params = [params[key] for key in keys]

    # Replace each string formatting directive with a question mark (?)
    modified_template = format_directive_pattern.sub('?', rendered)

    return modified_template, positional_params


def sql_query(query: str,
              params: dict | None = None,
              callback: FunctionType | None = None) -> tuple[list, list]:
    """Executes a SQL query using the given parameters.

    Uses jinjasql to render the query and perform parameter
    substitution. Optional callable object 'callback' with a single
    argument 'cursor' will be executed before the query.

    Returns a tuple (headers, rows)

    """

    params = params or {}
    sql, bind_params = render_template(query, params)

    conn = pyodbc.connect(CONNECTION_STRING)
    # TODO: figure out charcater encoding settings
    # conn.setdecoding(pyodbc.SQL_CHAR, encoding='utf8')
    # conn.setdecoding(pyodbc.SQL_WCHAR, encoding='utf8')
    # conn.setencoding(encoding='utf8')

    with conn:
        cursor = conn.cursor()
        if callback:
            callback(cursor=cursor)

        cursor.execute(sql, bind_params)
        headers = [column[0] for column in cursor.description]
        rows = deserialize_json(headers, cursor.fetchall())
        headers = [name.replace('__json', '') for name in headers]
        return (headers, rows)


def create_and_load_temp_table(cursor, sql_cmd: str, rows: list):
    """Create and load a temporary table using the provided schema
    and data files. Rows is a list of dicts.
    """

    if mo := re.search(r'create table ([#a-z_]+)', sql_cmd, re.I):
        tablename = mo.groups()[0]
    else:
        raise ValueError('could not find table name')

    log.info(f"Creating temporary table {tablename}")
    cursor.execute(sql_cmd)
    result = cursor.execute(f'select * from {tablename}')
    headers = [desc[0] for desc in result.description]

    log.info("Loading data into temporary table")
    placeholders = ','.join(['?'] * len(headers))
    sql_insert = f'insert into "{tablename}" ({', '.join(headers)}) values ({placeholders})'
    log.info(sql_insert)

    if len(headers) == 1:
        key = headers[0]
        vals = [(row[key],) for row in rows]
    else:
        getter = itemgetter(*headers)
        vals = [getter(row) for row in rows]

    cursor.executemany(sql_insert, vals)


def deserialize_json(headers: list, rows: list) -> list:
    json_cols = [i for i, name in enumerate(headers) if name.endswith('__json')]
    for row in rows:
        for i in json_cols:
            row[i] = json.loads(row[i].replace('\\\\n', '\\n'))
    return rows


def as_dicts(headers: list, rows: list):
    """Converts a list of rows and headers into a list of dictionaries"""
    return [dict(zip(headers, row)) for row in rows]
