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

from functools import wraps
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

from .server import ServerAdapter
from .server import WSGIRefServer
from .template import Loader
from .wrappers import Request, Response
from .router import Router

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
        handler = None
        try:
            handler, args = self._router.get(
                self._request.path, self._request.method)
        except TypeError:
            self.redirect("404")
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
