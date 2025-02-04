from dawgtools import db


def normalize_ws(text):
    # Remove all line breaks and ensure a single space between words
    return ' '.join(text.split())


def test_simple_template():
    template = "SELECT * FROM users WHERE name = %(name)s"
    params = {"name": "Alice"}
    expected_query = "SELECT * FROM users WHERE name = ?"
    expected_params = ["Alice"]
    result = db.render_template(template, params)
    assert (normalize_ws(result[0]), result[1]) == (normalize_ws(expected_query), expected_params)


def test_with_jinja_conditionals():
    template = """
    SELECT * FROM products WHERE price < %(max_price)s
    {% if in_stock %}
    AND stock > 0
    {% endif %}
    """
    params = {"max_price": 500, "in_stock": True}
    expected_query = """
    SELECT * FROM products WHERE price < ?
    AND stock > 0
    """
    expected_params = [500]
    result = db.render_template(template, params)
    assert (normalize_ws(result[0]), result[1]) == (normalize_ws(expected_query), expected_params)


def test_complex_template():
    template = """
    SELECT * FROM orders WHERE customer_id = %(customer_id)s
    {% if status %}
    AND status = %(status)s
    {% endif %}
    """
    params = {"customer_id": 42, "status": "shipped"}
    expected_query = """
    SELECT * FROM orders WHERE customer_id = ?
    AND status = ?
    """
    expected_params = [42, "shipped"]
    result = db.render_template(template, params)
    assert (normalize_ws(result[0]), result[1]) == (normalize_ws(expected_query), expected_params)
