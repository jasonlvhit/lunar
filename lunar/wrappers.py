import sys
import cgi
import threading

from collections import MutableMapping

if sys.version < '3':
    import httplib
    from Cookie import SimpleCookie
    from urlparse import parse_qs
else:
    import http.client as httplib
    from http.cookies import SimpleCookie
    from urllib.parse import parse_qs

"""
A simple wrapper for base WSGI request and response.
"""


class HttpHeaders(MutableMapping):

    """ Wrapper for Http-like headers.

        Dict-like key-value store, but keys are Http-Header-Case foramt.
        value is a list, but the magic method __getitem__ will only return the
        latest value added.
    """

    def __init__(self, *args, **kwargs):
        self._dict = dict((HttpHeaders.normalize_key(k), [v]) for (
            k, v) in dict(*args, **kwargs).items())

    def __setitem__(self, key, value):
        self._dict.setdefault(HttpHeaders.normalize_key(key), []).append(value)

    def __getitem__(self, key):
        return self._dict[HttpHeaders.normalize_key(key)][-1]

    def __contains__(self, key):
        return HttpHeaders.normalize_key(key) in self._dict

    def __delitem__(self, key):
        del self._dict[HttpHeaders.normalize_key(key)]

    def __len__(self):
        return len(self._dict)

    def __iter__(self):
        return iter(self._dict)

    def append(self, key, value):
        self._dict.setdefault(HttpHeaders.normalize_key(key), []).append(value)

    def get_list(self, key):
        return self._dict.get(HttpHeaders.normalize_key(key), [])

    def as_list(self):
        return [(k, self.__getitem__(k)) for k in self._dict.keys()]

    @staticmethod
    def normalize_key(key):
        """ Converts a key to Http-Header-Case

        """
        return "-".join([w.capitalize() for w in key.split("-")])


class BaseObject(threading.local):

    """Base class for request and response.
    Provide a thread safe space.
    """
    pass


class Request(BaseObject):

    def __init__(self, environ=None):
        self.environ = {} if environ is None else environ
        self._args = {}
        self._forms = {}

    def bind(self, environ):
        self.environ = environ

    @property
    def forms(self):
        if self._forms:
            return self._forms
        d = cgi.FieldStorage(
            fp=self.environ['wsgi.input'], environ=self.environ)
        for k in d:
            if isinstance(d[k], list):
                self._forms[k] = [v.value for v in d[k]]
            elif d[k].filename:
                self._forms[k] = d[k]
            else:
                self._forms[k] = d[k].value
        return self._forms

    @property
    def args(self):
        if self._args:
            return self._args
        d = parse_qs(self.query)
        for k, v in d.items():
            if len(v) == 1:
                self._args[k] = v[0]
            else:
                self._args[k] = v
        return self._args

    @property
    def path(self):
        return '/' + self.environ.get("PATH_INFO", '').lstrip('/')

    @property
    def headers(self):
        return self.environ

    @property
    def method(self):
        return self.environ.get('REQUEST_METHOD', 'GET')

    @property
    def query(self):
        return self.environ.get('QUERY_STRING', '')

    @property
    def cookies(self):
        return SimpleCookie(self.environ.get('HTTP_COOKIE', ''))

    @property
    def if_modified_since(self):
        return self.environ.get('HTTP_IF_MODIFIED_SINCE', '')


class Response(BaseObject):

    def __init__(self, body, code=200, content_type='text/html'):
        self.headers = HttpHeaders()
        self._cookies = None
        self._status = code
        self.content_type = content_type

        # body
        self._body = None
        self.set_body(body)

    @property
    def cookies(self):
        if not self._cookies:
            self._cookies = SimpleCookie()
        return self._cookies

    def set_cookie(self, key, value, **kargs):
        self.cookies[key] = value
        for k in kargs:
            self.cookies[key][k] = kargs[k]

    @property
    def status(self):
        return " ".join([str(self._status), httplib.responses.get(self._status)])

    def set_status(self, s):
        self._status = s

    @property
    def headerlist(self):
        return self.headers.as_list()

    @property
    def body(self):
        return self._body

    def set_body(self, body):
        self._body = str(body)
        # Python 3 bytes hack
        if sys.version > '3':
            self._body = bytes(self._body, 'utf-8')

    def get_content_type(self):
        return self.headers['Content-Type']

    def set_content_type(self, value):
        self.headers['Content-Type'] = value

    content_type = property(
        get_content_type, set_content_type, None, get_content_type.__doc__)
