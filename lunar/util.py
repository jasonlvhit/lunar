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

    @property
    def empty(self):
        return len(self._Stack) == 0


class LRUCache(object):

    """ Simple LRU cache for template instance caching.

        in fact, the OrderedDict in collections module or
        @functools.lru_cache is working well too.

    """

    def __init__(self, capacity):
        self.capacity = capacity
        self.cache = OrderedDict()

    def get(self, key):
        """ Return -1 if catched KeyError exception.

        """
        try:
            value = self.cache.pop(key)
            self.cache[key] = value
            return value
        except KeyError:
            return -1

    def set(self, key, value):
        try:
            self.cache.pop(key)
        except KeyError:
            if len(self.cache) >= self.capacity:
                self.cache.popitem(last=False)
        self.cache[key] = value
