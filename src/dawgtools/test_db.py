from dawgtools import db


def test_db():
    tests = [
        # Test 1: Simple substitution
        {
            'template_string': "SELECT * FROM table WHERE col1 = {{ val }}",
            'kwargs': {'val': 10},
            'expected_output': ("SELECT * FROM table WHERE col1 = ?", [10])
        },
        # Test 2: Multiple parameters
        {
            'template_string': "INSERT INTO table (col1, col2) VALUES ({{ val1 }}, {{ val2 }})",
            'kwargs': {'val1': 20, 'val2': 30},
            'expected_output': ("INSERT INTO table (col1, col2) VALUES (?, ?)", [20, 30])
        },
        # Test 3: No keyword parameters
        {
            'template_string': "DELETE FROM table WHERE col1 > 5",
            'kwargs': {},
            'expected_output': ("DELETE FROM table WHERE col1 > 5", [])
        },
        # Test 4: Dynamic values in string
        {
            'template_string': "UPDATE table SET col1 = {{ val }} WHERE col2 < 100",
            'kwargs': {'val': 40},
            'expected_output': ("UPDATE table SET col1 = ? WHERE col2 < 100", [40])
        },
        # Test 5: Repeated parameters
        {
            'template_string': "SELECT * FROM table WHERE col1 = {{ val }} AND col2 = {{ val }}",
            'kwargs': {'val': 50},
            'expected_output': ("SELECT * FROM table WHERE col1 = ? AND col2 = ?", [50, 50])
        },
        # Test 6: Parameters in different order
        {
            'template_string': "UPDATE table SET col1 = {{ val2 }}, col2 = {{ val1 }}",
            'kwargs': {'val1': 100, 'val2': 200},
            'expected_output': ("UPDATE table SET col1 = ?, col2 = ?", [200, 100])
        }
    ]

    for i, test in enumerate(tests):
        result = db.render_template(test['template_string'], params=test['kwargs'])
        assert result == test['expected_output']
