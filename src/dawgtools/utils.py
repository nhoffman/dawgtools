import sys
from datetime import datetime
from decimal import Decimal
import json


class StdOut:
    def __init__(self, *args, **kwargs):
        pass

    def __enter__(self):
        self.fobj = sys.stdout
        return self.fobj

    def __exit__(self, exc_type, exc_value, traceback):
        pass


class MyJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, Decimal):
            return int(obj)
        return super().default(obj)
