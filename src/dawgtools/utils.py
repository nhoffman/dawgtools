import sys


class StdOut:
    def __init__(self, *args, **kwargs):
        pass

    def __enter__(self):
        self.fobj = sys.stdout
        return self.fobj

    def __exit__(self, exc_type, exc_value, traceback):
        pass



