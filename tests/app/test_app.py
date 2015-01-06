import os
import sys
import time
import unittest

if sys.version < '3':
    try:
        from cStringIO import StringIO
    except ImportError:
        import StringIO

else:
    from io import BytesIO as StringIO

from lunar.lunar import Lunar, LunarException, _Stack
from lunar.router import RouterException


def start_response(status, headerlist):
    pass


class SimpleClass(object):
    pass

app = Lunar('__main__')

dirname, filename = os.path.split(os.path.abspath(__file__))
app.root_path = dirname


@app.route('/', methods=["GET", "POST"])
def index():
    return "Hello, lunar!"

#/args?key=lunar&count=4


@app.route('/test_args', methods=["GET"])
def args():
    return app.request.args["key"], app.request.args["count"]


@app.route('/test_post', methods=['GET', 'POST'])
def post():
    if app.request.method == 'GET':
        return app.render('test_post.html')
    return app.request.forms["title"], app.request.forms["tag"]


@app.route('/show/<int:id>')
def sync_args(id):
    return id

# template


@app.route('/template')
def template():
    return app.render('index.html')


@app.route('/url_for_with_args')
def url_for_with_args():
    return app.url_for(sync_args, id=1)


@app.route('/url_for_normal_func')
def url_for_with_args():
    return 'normal function'


@app.route('/url_for_static')
def url_for_static():
    return app.url_for('static', 'style.css')


@app.route('/push_session')
def push_session():
    app.session['lunar'] = "a web framework"
    return app.session['lunar'].value


@app.route('/show_session')
def show_session():
    return app.session['lunar'].value


@app.route('/json')
def json_request():
    return app.jsonify({"BJ": "Beijing"})


@app.route('/test_redirect')
def redirect():
    return app.redirect('/')


@app.route('/redirect_with_args')
def redirect_with_url():
    return app.redirect(app.url_for(test_sync_args, id=1))


@app.route('/test_handler_exception')
def handler_exception():
    raise RuntimeError


class StackTest(unittest.TestCase):

    def setUp(self):
        self.stack = _Stack()

    def tearDown(self):
        self.stack = None

    def test_push_stack(self):
        self.stack.push(1)
        self.assertEqual(self.stack.top(), 1)

    def test_pop_stack(self):
        self.assertEqual(len(self.stack), 0)
        self.stack.push(1)
        self.assertEqual(len(self.stack), 1)
        self.assertEqual(self.stack.pop(), None)
        self.assertEqual(len(self.stack), 0)

    def test_empty_stack(self):
        self.assertTrue(self.stack.empty())
        self.stack.push(1)
        self.assertFalse(self.stack.empty())


class AppTest(unittest.TestCase):

    def tearDown(self):
        app.static_url_cache.clear()

    def test_route_wrapper_with_illegel_arg(self):
        self.assertRaises(RouterException, app.route, None)

    def test_run_with_not_subclass_of_server_adapter(self):
        self.assertRaises(RuntimeError, app.run, server=SimpleClass)

    def test_static_url_for_cache(self):
        env = {
            'HTTP_HOST': 'localhost',
            'wsgi.url_scheme': 'http',
            'SERVER_PORT': '80',
        }
        r = app(env, start_response)
        url = app.url_for('static', 'style.css')
        self.assertEqual(
            app.static_url_cache, {'style.css': 'http://localhost/static/style.css'})
        self.assertEqual(
            app.url_for('static', 'style.css'), 'http://localhost/static/style.css')

    def test_static_url_for_with_http_standard_port(self):
        env = {
            'HTTP_HOST': 'localhost',
            'wsgi.url_scheme': 'http',
            'SERVER_PORT': '80',
        }
        r = app(env, start_response)
        self.assertEqual(
            app.url_for('static', 'style.css'), 'http://localhost/static/style.css')

    def test_static_url_for_with_http_non_standard_port(self):
        env = {
            'SERVER_NAME': 'www.example.com',
            'wsgi.url_scheme': 'http',
            'SERVER_PORT': '8000'
        }
        r = app(env, start_response)
        self.assertEqual(app.url_for('static', 'style.css'),
                         'http://www.example.com:8000/static/style.css')

    def test_static_url_for_with_https_standard_port(self):
        env = {
            'HTTP_HOST': 'localhost',
            'wsgi.url_scheme': 'https',
            'SERVER_PORT': '443'
        }
        r = app(env, start_response)
        self.assertEqual(
            app.url_for('static', 'style.css'), 'https://localhost/static/style.css')

    def test_static_url_for_with_https_non_standard_port(self):
        env = {
            'SERVER_NAME': 'www.example.com',
            'wsgi.url_scheme': 'https',
            'SERVER_PORT': '400'
        }
        r = app(env, start_response)
        self.assertEqual(app.url_for('static', 'style.css'),
                         'https://www.example.com:400/static/style.css')

    def test_json_request(self):
        env = {
            'HTTP_HOST': 'localhost',
            'wsgi.url_scheme': 'http',
            'SERVER_PORT': '80',
            'PATH_INFO': '/json'
        }
        r = app(env, start_response)
        self.assertEqual(app._response.get_content_type(), 'application/json')

    def test_not_found(self):
        env = {
            'HTTP_HOST': 'localhost',
            'wsgi.url_scheme': 'http',
            'SERVER_PORT': '80',
            'PATH_INFO': '/hello'
        }
        r = app(env, start_response)
        self.assertEqual(app._response.status, '404 Not Found')

    def test_redirect(self):
        env = {
            'HTTP_HOST': 'localhost',
            'wsgi.url_scheme': 'http',
            'SERVER_PORT': '80',
            'PATH_INFO': '/test_redirect'
        }
        r = app(env, start_response)
        self.assertEqual(app._response.status, '302 Found')
        self.assertEqual(app._response.headers['Location'], '/')

    def test_not_modified(self):
        env = {
            'HTTP_HOST': 'localhost',
            'wsgi.url_scheme': 'http',
            'SERVER_PORT': '80',
            'PATH_INFO': '/static/style.css'
        }
        r = app(env, start_response)
        last_modified_str = app._response.headers['Last-Modified']
        last_modified_time = time.strptime(
            last_modified_str, "%a, %d %b %Y %H:%M:%S %Z")

        a_year_after = time.strftime(
            "%a, %d %b %Y %H:%M:%S UTC", last_modified_time)

        env = {
            'HTTP_HOST': 'localhost',
            'wsgi.url_scheme': 'http',
            'SERVER_PORT': '80',
            'PATH_INFO': '/static/style.css',
            'HTTP_IF_MODIFIED_SINCE': a_year_after
        }
        r = app(env, start_response)
        self.assertEqual(app._response.status, '304 Not Modified')

    def test_500_internal_error(self):
        env = {
            'HTTP_HOST': 'localhost',
            'wsgi.url_scheme': 'http',
            'SERVER_PORT': '80',
            'PATH_INFO': '/test_handler_exception'
        }
        r = app(env, start_response)
        self.assertEqual(app._response.status, '500 Internal Server Error')

    def test_handle_get_query_string(self):
        env = {
            'HTTP_HOST': 'localhost',
            'wsgi.url_scheme': 'http',
            'SERVER_PORT': '80',
            'PATH_INFO': '/test_args',
            'QUERY_STRING': 'key=test&count=5'
        }
        r = app(env, start_response)
        self.assertEqual(app._response.status, '200 OK')
        self.assertEqual(app._request.args['key'], 'test')

    def test_handle_post_query(self):
        env = {
            'HTTP_HOST': 'localhost',
            'wsgi.url_scheme': 'http',
            'SERVER_PORT': '80',
            'PATH_INFO': '/test_args',
            'wsgi.input': StringIO(b'title=test&tag=python'),
            'REQUEST_METHOD': 'POST'
        }
        r = app(env, start_response)
        self.assertEqual(app._request.forms['title'], 'test')
        self.assertEqual(app._request.forms['tag'], 'python')

    def test_handle_router_args(self):
        env = {
            'HTTP_HOST': 'localhost',
            'wsgi.url_scheme': 'http',
            'SERVER_PORT': '80',
            'PATH_INFO': '/show/1',
        }
        r = app(env, start_response)
        self.assertEqual(app._response.status, '200 OK')
        self.assertEqual(app._response.body, b'1')

    def test_handle_static(self):
        env = {
            'HTTP_HOST': 'localhost',
            'wsgi.url_scheme': 'http',
            'SERVER_PORT': '80',
            'PATH_INFO': '/static/style.css'
        }
        r = app(env, start_response)
        self.assertEqual(app._response.status, '200 OK')
        self.assertEqual(app._response.content_type, 'text/css')

    def test_handle_static_not_found(self):
        env = {
            'HTTP_HOST': 'localhost',
            'wsgi.url_scheme': 'http',
            'SERVER_PORT': '80',
            'PATH_INFO': '/static/main.css'
        }
        r = app(env, start_response)
        self.assertEqual(app._response.status, '404 Not Found')
