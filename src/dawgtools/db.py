import logging
import re

from jinja2 import Template
import pyodbc

log = logging.getLogger(__name__)


CONNECTION_STRING = ';'.join([
    'DRIVER={ODBC Driver 17 for SQL Server}',
    'SERVER=am-dawg-sql-trt',
    'Trusted_Connection=yes'
])


def render_template(query: str, params: dict) -> tuple[str, list]:
    """Renders a jinja2 template using the given parameters using
    jinjasql and return the rendered SQL and parameters

    """

    template = Template(query)
    context = {key: '?' for key in params.keys()}

    # Render the template, replacing all variables with '?'
    rendered = template.render(**context)

    # Gather the positional arguments in the order they appear
    template_variables = re.findall(r'{{\s*(\w+)\s*}}', query)
    positional_args = [params[var] for var in template_variables if var in params]

    return rendered, positional_args


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
