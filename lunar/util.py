# Some useful functions

from collections import OrderedDict
from time import time
from itertools import islice


def html_escape(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')\
            .replace('"', '&quot;').replace("'", '&#039;')


def sqlite_escape(s):
    return s.replace('\'', '\'\'')
