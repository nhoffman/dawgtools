import logging
import re
from pathlib import Path

from jinja2 import Template
import pyodbc

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


def sql_query(query: str, params: dict = None) -> tuple[list, list]:
    """Executes a SQL query using the given parameters.

    Uses jinjasql to render the query and perform parameter substitution.

    Returns a tuple (headers, rows)
    """

    params = params or {}
    sql, bind_params = render_template(query, params)

    conn = pyodbc.connect(CONNECTION_STRING)
    with conn:
        cursor = conn.cursor()
        cursor.execute(sql, bind_params)
        headers = [column[0] for column in cursor.description]
        rows = cursor.fetchall()
        return (headers, rows)



def as_dicts(headers: list, rows: list):
    """Converts a list of rows and headers into a list of dictionaries"""
    return [dict(zip(headers, row)) for row in rows]
