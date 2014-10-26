#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Pumpkin. A simple WSGI based webframework for learning.

Pumpkin是一个玩具式的网络框架，基于PEP333和它的进化版PEP3333，它包括一个Router，
一个Template engine，一个简单的WSGI Request和Response的封装，没有任何第三方包的依赖。
项目会不断的演化，在你看到这句话的时候，这个项目还是千疮百孔，下一步会修复很多bug，
重构一些代码，可能会加入基于epoll或者select的异步请求支持。

查看example来看看这是怎么运作的。

Pumpkin is a WSGI based webframework in pure Python, without any third-party dependency. 
Pumpkin include a simple router, which provide the request routing, a template engine 
for template rendering, a simple wrapper for WSGI request and response.

Happy hacking.

About pumpkin：

洋葱、萝卜和番茄不相信世界上有南瓜这个东西，它们认为那只是空想。南瓜默默不说话，它只是继续成长。
这句话来自《当世界年纪还小的时候》这本书的封底，希望我们都能成长为一只大大的南瓜。

"""


import cgi
import os
import re
import sys

import threading

from functools import wraps
from wsgiref.util import setup_testing_defaults
from wsgiref.simple_server import make_server
from Queue import Queue

from collections import MutableMapping

if sys.version < '3':
    string_escape = 'string-escape'

    import httplib
    from Cookie import SimpleCookie
    from urlparse import parse_qs
else:
    string_escape = 'unicode_escape'

    import http.client as httplib
    from http.cookies import SimpleCookie
    from urllib.parse import parse_qs

try:
    import pkg_resources
    pkg_resources.resource_stream
except (ImportError, AttributeError):
    pkg_resources = None


"""
A simple router.
"""


class RouterException(Exception):
    pass


class Router(object):

    """Router object for request routing.
    """

    def __init__(self):
        self.rules = {}
        '''
        '/'
        '/hello'
        '/hello/pumpkin'
        '/hello/pumpkin/<int:id>'
        '''
        # caution!!!!
        # weird in python 3: get nothing to repeat error in python 3
        # http://stackoverflow.com/questions/3675144/regex-error-nothing-to-repeat
        self.url_pattern = re.compile(
            r'(?P<prefix>(/\w*)+)(?P<suffix><(?P<type>\w*)?:(?P<arg>\w*)>)?')

        # methods
        self.methods = {}
        self.methods.setdefault("GET", [])
        self.methods.setdefault("POST", [])
        self.methods.setdefault("DELETE", [])
        self.methods.setdefault("PUT", [])

    def register(self, path, fn, methods):
        if not callable(fn):
            raise RouterException("Router only accept callable object.")

        for m in methods:
            self.methods[m].append(fn)

        g = self.url_pattern.match(path)
        if not g:
            raise RouterException(
                "Router rules : %s can not be accepted." % path)
        p = g.group('prefix')
        if g.group('suffix'):
            assert g.group('type') == 'int', g.group('type')
            p += '(?P<args>\d+)'
            self.rules[(re.compile(p), g.group('arg'))] = fn
        else:
            self.rules[p] = fn

    def __call__(self, p, method='GET'):
        return self.get(p, mathod)

    def get(self, path, method='GET'):
        f, args = self._match_path(path)
        if not f:
            return None
        method = method.upper()
        if f not in self.methods.get(method):
            raise RouterException(
                "Request method %s not allowed in this app." % method)
        return (f, args)

    def _match_path(self, p):
        for k in self.rules:
            if isinstance(k, str):
                if k == p:
                    return self.rules[k], None
            elif isinstance(k[0], type(re.compile('dommy'))):
                _g = k[0].match(p)
                if _g:
                    return (self.rules[k], {k[1]: _g.group('args')})

    def url_for(self, fn):
        if not callable(object):
            raise RouterException(
                "router url_for method only accept callable object.")
        for k, v in self.rules.items():
            if v == fn:
                return k
        raise RouterException(
            "callable object doesn't matched any routing rule.")

    def all_callables(self):
        return self.rules.values()

"""
A simple template engine.
"""


class Walker(object):

    """ Read the source code, provide the token for
        Parser.

    """

    def __init__(self, text):
        self.text = text
        self.cur = 0
        # re token
        self.token = re.compile(r'''
            {{\s+(?P<var>.+?)\s+}} # variable
            | # or
            {%\s+(?P<endblock>end(if|for|try|while|block))\s+%} # endblock
            | # or
            {%\s+(?P<statement>(?P<keyword>\w+)\s*(.*?))\s+%} # statement
            ''', re.VERBOSE)

        self.buffer = []

    @property
    def next_token(self):
        p = self.token.search(self.remain)
        if not p:
            return None
        s = p.start()
        self.buffer.append(self.remain[:s].encode(string_escape))
        self.cur += (s + len(p.group()))
        return p

    @property
    def buffer_before_token(self):
        r = ''.join(i for i in map(lambda x: x.decode('utf-8'), self.buffer))
        self.buffer = []
        return r

    @property
    def empty(self):
        return self.cur >= len(self.text)

    @property
    def remain(self):
        return self.text[self.cur:]

    @property
    def extends(self):
        """The {% extends %} tag is the key here. 
        It tells the template engine that this template "extends" another template. 
        When the template system evaluates this template, first it locates the parent. 

        The extends tag should be the first tag in the template.
        """
        p = re.compile(r'^{%\s+(extends\s*(?P<parent>.*))\s+%}')
        e = p.match(self.text)
        if not e:
            return None
        self.cur += len(e.group())
        return e.group('parent')


class Writer(object):

    """ Writer is a important part of template engine, which provide
        methods for different tokens and blocks. Writer consturct a 
        intermediate code for Python runtime compilinng and excuting,
        the main class below 'Template ' will use this code for rendering 
        and code generating.
    """

    def __init__(self):
        self.co = []
        self._blocks = {}

    def dispatcher(fn):
        @wraps(fn)
        def wrapper(self, s, indent, block):
            p = fn(self, s, indent, block)
            if block:
                self._blocks.get(block).append(p)
            else:
                self.co.append(p)
        return wrapper

    @dispatcher
    def write(self, s, indent, block=None):
        return ''.join([' ' * indent, '_stdout.append(\'\'\' ', s, ' \'\'\')\n'])

    @dispatcher
    def write_var(self, s, indent, block=None):
        return ''.join([' ' * indent, '_stdout.append(str(', s, '))\n'])

    @dispatcher
    def write_key(self, s, indent, block=None):
        return ''.join([' ' * indent, s, '\n'])

    def write_child(self, c):
        self.co.append(''.join(['block%', c, '\n']))

    def open_block(self, v):
        self._blocks.setdefault(v, [])

    def write_snippet(self, snippet, indent, block=None):
        p = re.compile(r'\n')
        self.co.append(
            p.sub(''.join(['\n', ' ' * indent]), self.shave(''.join(snippet))))

    def shave(self, s):
        p = re.compile(r'(\s+\n)+')
        return p.sub('\n', s)


class TemplateException(Exception):
    pass


class Template(object):

    def __init__(self, source, autoescape=True, path=None):
        self.co = None
        self.walker = Walker(source)
        self.writer = Writer()
        self.parents = None
        self.path = path
        self.autoescape = autoescape
        if source:
            self.co = self.parse().compile()

    def render(self, *args, **context):
        if self.autoescape:
            for (k, v) in context.items():
                if isinstance(v, str):
                    context[k] = self.html_escape(v)

        context['_stdout'] = []
        exec(self.co, context)
        return self.shave_newline(''.join(context['_stdout']))

    def compile(self):
        if self.parents:
            self.writer.co = self.parents.writer.co
        pattern = re.compile(r'block%(?P<name>\w+)')
        _t = ''.join(self.writer.co)
        for g in pattern.finditer(_t):
            if g.group('name') in self.writer._blocks.keys():
                _t = _t.replace(
                    g.group(), ''.join(self.writer._blocks[g.group('name')]))
        # print(_t)
        return compile(_t, '<string>', 'exec')

    def parse(self):
        indent = 0
        operator = ['if', 'try', 'while', 'for']
        intermediate = ['else', 'elif', 'except', 'finally']
        in_block = []

        def in_block_top():
            if len(in_block):
                return in_block[len(in_block) - 1]
            return None
        _tmp = self.walker.extends
        if _tmp:
            self.parents = Loader(self.path).load(self.shave_dot(_tmp))
        while not self.walker.empty:
            token = self.walker.next_token
            if not token:
                self.writer.write(self.walker.remain, indent, in_block_top())
                break
            self.writer.write(
                self.walker.buffer_before_token, indent, in_block_top())
            variable, endblock, end, statement, keyword, suffix = token.groups()
            # print(token.groups())
            if suffix:
                suffix = self.shave_dot(suffix)
            if variable:
                self.writer.write_var(variable, indent, in_block_top())
            elif endblock:
                if end is 'block' and self.parents:
                    in_block.pop()
                indent -= 1
            elif keyword:
                if keyword == "include":
                    c = Loader(self.path).load(suffix).r_co
                    self.writer.write_snippet(c, indent, in_block_top())
                    continue
                elif keyword == "block":
                    if not self.parents:
                        self.writer.write_child(suffix)
                        continue
                    self.writer.open_block(suffix)
                    in_block.append(suffix)
                    continue
                elif keyword not in (intermediate + operator):
                    self.writer.write_key(
                        ' '.join([keyword, suffix]), indent, in_block_top())
                    continue
                if keyword in intermediate:
                    indent -= 1
                self.writer.write_key(
                    ' '.join([keyword, suffix, ':']), indent, in_block_top())
                indent += 1
            else:
                raise TemplateException('fuck.')
        return self

    def html_escape(self, s):
        return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')\
                .replace('"', '&quot;').replace("'", '&#039;')

    @property
    def r_co(self):
        return self.writer.co

    def shave_dot(self, s):
        return re.sub(r'\'|\"', '', s)

    def shave_slash(self, s):
        return re.sub(r'\\n', '\n', s)

    def shave_newline(self, s):
        return re.sub(r'(\s+\n)+', '\n', s)


class Loader(object):

    def __init__(self, root='', e=Template):
        if not root.endswith('\\'):
            root += '\\'
        self.root = root
        self.engine = e

    def update_template_engine(self, e):
        self.engine = e

    def load(self, filename):
        p = '\\'.join([self.root, filename])
        # print(p)
        if not os.path.isfile(p):
            raise TemplateException("Template file %s didn't existed." % p)
        with open(p) as f:
            return self.engine(f.read(), path=self.root)

# template safe escape


def unescape(s):
    """ unescape html tokens.
        <p>{{ unescape(content) }}</p>
    """
    return s.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')\
        .replace('&quot;', '"').replace('&#039;', "'")


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

    """
    @property
    def url(self):
        return '\\'.join([self.environ.get('wsgi.url_scheme', '')]) 
    """


class Response(BaseObject):

    def __init__(self, body):
        self.headers = HttpHeaders()
        self._cookies = None
        self._status = 200
        self.content_type = 'text/html'

        # body
        self._body = body

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

    def get_content_type(self):
        return self.headers['Content-Type']

    def set_content_type(self, value):
        self.headers['Content-Type'] = value

    content_type = property(
        get_content_type, set_content_type, None, get_content_type.__doc__)


"""
The Main object of pumpkin.
"""


class _Stack(object):

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

    def empty(self):
        return True if len(_Stack) == 0 else False

    def __repr__(self):
        return "_app_stack with %s applications" % (len(self))


class Pumpkin(object):

    """Main object of this funny web frameWork
    """

    def __init__(self, pkg_name, template='template', static='static'):
        # router
        self._router = Router()

        # request and response
        self._request = Request()
        self._response = Response(None)

        # template
        self.package_name = pkg_name
        #: where is the app root located?
        self.root_path = self._get_package_path(
            self.package_name).replace('\\', '\\\\')  # '\u' escape

        self.loader = Loader('\\\\'.join([self.root_path, template]))

        # static file
        self.static_folder = static

        # session
        self._session = self._request.cookies

        # request_queue
        self._req_arg_queue = Queue()
        self._server_handler = None

        # push to the _app_stack
        global _app_stack
        _app_stack.push(self)

    def set_template_engine(self, engine):
        self.loader.update_template_engine(engine)

    def _get_package_path(self, name):
        """Returns the path to a package or cwd if that cannot be found."""
        try:
            return os.path.abspath(os.path.dirname(sys.modules[name].__file__))
        except (KeyError, AttributeError):
            return os.getcwd()

    def route(self, path=None, methods=['GET']):
        if path == None:
            raise RouterException
        methods = [m.upper() for m in methods]

        def wrapper(fn):
            self._router.register(path, fn, methods)
            return fn
        return wrapper

    @property
    def session(self):
        return self._session

    def run(self, server=WSGIRefServer, host='localhost', port=8000):
        if isinstance(server, type) and issubclass(server, ServerAdapter):
            server = server(host=host, port=port)

        if not isinstance(server, ServerAdapter):
            raise RuntimeError("Server must be a subclass of ServerAdapter.")

        print("running on %s:%s" % (host, port))
        try:
            server.run(self)
        except KeyboardInterrupt:
            pass

    def render_template(self, file, **context):
        # print(self.loader.load(file).r_co)
        app_namespace = sys.modules[self.package_name].__dict__
        context.update(globals())
        context.update(app_namespace)
        return self.loader.load(file).render(**context)

    """
    def redirect(self, path, next=None, **kwargs):
        # redirect just push the request into the queue of requests,
        # and in the main loop of execution, all the jobs in queue will be 
        # executed in turn.
        
        self._req_queue.put((path, 'GET', kwargs))
        if next:
            self._req_queue.put((next, 'GET', None))

    def redirect(self, path, **kwargs):
        self._request.environ['PATH_INFO'] = path
        self._request.environ['REQUEST_METHOD'] = 'GET'
        self._req_arg_queue.put((path, 'GET', kwargs))
        return self.__call__(self.request.environ, self._server_handler)

    """

    def redirect(self, path):
        pass

    def url_for(self, fn):
        return self._router.url_for(fn)

    def load_static(self, filename, path=None):
        """ load static files:
            <link type="text/css" rel="stylesheet" href="{{ app.load_static('style.css') }}" />
        """
        if path:
            return '\\'.join([self.root_path, path, filename]).replace("\\\\", "\\")
        return '\\'.join([self.root_path, self.static_folder, filename]).replace("\\\\", "\\")

    @property
    def request(self):
        return self._request

    @property
    def response(self):
        return self._response

    def __call__(self, environ, start_response):
        self._server_handler = start_response
        self._request.bind(environ)
        handler, args = self._router.get(
            self._request.path, self._request.method)
        if not handler:
            self.redirect("404")
        try:
            if args:
                body = handler(**args)
            else:
                body = handler()
            self._response.set_body(body=body)
        except Exception:
            self._response.set_status(500)
 
        start_response(self._response.status, self._response.headerlist)
        return [self._response.body]

"""
Bottle-like Servers strategy.

Method Pumpkin.run accept a subclass of ServerAdapter, create a server 
instance and run applications using the run interface provided by ServerAdapter.

So the server must implement the interface 'run' provided by ServerAdapter.
"""


class ServerAdapter(object):

    def __init__(self, host="127.0.0.1", port=8000):
        self.host = host
        self.port = port

    def __repr__(self):
        return "%s (%s:%s)" % (self.__class__.__name__, self.host, self.port)

    def run(self, app):
        pass


class WSGIRefServer(ServerAdapter):

    def run(self, app):
        from wsgiref.simple_server import make_server
        httpd = make_server(self.host, self.port, app)
        httpd.serve_forever()

# tornado server for test and example.


class TornadoServer(ServerAdapter):

    def run(self, handler):
        import tornado.wsgi
        import tornado.httpserver
        import tornado.ioloop
        container = tornado.wsgi.WSGIContainer(handler)
        server = tornado.httpserver.HTTPServer(container)
        server.listen(port=self.port, address=self.host)
        tornado.ioloop.IOLoop.instance().start()

"""
default methods and properties
"""

# global app stack.
_app_stack = _Stack()

# default app
default_app = _app_stack.top()
if not default_app:  # hack for shell
    default_app = Pumpkin('/')

# shell
request = _app_stack.top().request
response = _app_stack.top().response
session = _app_stack.top().session
