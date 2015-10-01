# Some useful goodies

import threading

from collections import OrderedDict
from time import time
from itertools import islice


def html_escape(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')\
            .replace('"', '&quot;').replace("'", '&#039;')


def sqlite_escape(s):
    return s.replace('\'', '\'\'')


class _Stack(threading.local):

    def __init__(self):
        self._Stack = []

    def push(self, app):
        self._Stack.append(app)

    def pop(self):
        try:
            self._Stack.pop()
        except IndexError:
            return None

    def top(self):
        try:
            return self._Stack[-1]
        except IndexError:
            return None

    def __len__(self):
        return len(self._Stack)

    def __str__(self):
        return str(self._Stack)

    def empty(self):
        return len(self._Stack) == 0
