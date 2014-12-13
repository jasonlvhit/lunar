import os
import unittest
from pumpkin.pumpkin import Pumpkin

def start_response(status, headerlist):
    pass

app = Pumpkin('__main__')

dirname, filename = os.path.split(os.path.abspath(__file__))
app.root_path = dirname

@app.route('/', methods=["GET", "POST"])
def index():
    return "Hello, Pumpkin!"

#/args?key=pumpkin&count=4
@app.route('/test_args', methods=["GET"])
def args():
    return app.request.args["key"], app.request.args["count"]

@app.route('/show/<int:id>')
def sync_args(id):
    return id
    
# template
@app.route('/template')
def template():
    return app.render_template('index.html')

@app.route('/url_for_with_args')
def url_for_with_args():
    return app.url_for(test_sync_args, id=1)

@app.route('/url_for_normal_func')
def url_for_with_args():
    return 'normal function'

@app.route('/url_for_static')
def url_for_static():
    return app.url_for('static', 'style.css')

@app.route('/push_session')
def push_session():
    app.session['pumpkin'] = "a web framework"
    return app.session['pumpkin'].value

@app.route('/show_session')
def show_session():
    return app.session['pumpkin'].value

@app.route('/test_redirect')
def redirect():
    return app.redirect('/')

@app.route('/redirect_with_args')
def redirect_with_url():
    return app.redirect(app.url_for(test_sync_args, id=1))


class AppTest(unittest.TestCase):
    def tearDown(self):
        app.static_url_cache.clear()

    def test_static_url_for_with_http_standard_port(self):
        env = {
            'HTTP_HOST': 'localhost',
            'wsgi.url_scheme':'http' ,
            'SERVER_PORT':'80',
        }
        r = app(env, start_response)
        self.assertEqual(app.url_for('static', 'style.css'), 'http://localhost/static/style.css')

    def test_static_url_for_with_http_non_standard_port(self):
        env = {
            'SERVER_NAME': 'www.example.com',
            'wsgi.url_scheme':'http' ,
            'SERVER_PORT':'8000'
        }
        r = app(env, start_response)
        self.assertEqual(app.url_for('static', 'style.css'), 'http://www.example.com:8000/static/style.css')

    def test_static_url_for_with_https_standard_port(self):
        env = {
            'HTTP_HOST': 'localhost',
            'wsgi.url_scheme':'https' ,
            'SERVER_PORT':'443'
        }
        r = app(env, start_response)
        self.assertEqual(app.url_for('static', 'style.css'), 'https://localhost/static/style.css')

    def test_static_url_for_with_https_non_standard_port(self):
        env = {
            'SERVER_NAME': 'www.example.com',
            'wsgi.url_scheme':'https' ,
            'SERVER_PORT':'400'
        }
        r = app(env, start_response)
        self.assertEqual(app.url_for('static', 'style.css'), 'https://www.example.com:400/static/style.css')

    def test_not_found(self):
        env = {
            'HTTP_HOST': 'localhost',
            'wsgi.url_scheme':'http' ,
            'SERVER_PORT':'80',
            'PATH_INFO':'/hello'
        }
        r = app(env, start_response)
        self.assertEqual(app._response.status, '404 Not Found')

    def test_redirect(self):
        env = {
            'HTTP_HOST': 'localhost',
            'wsgi.url_scheme':'http' ,
            'SERVER_PORT':'80',
            'PATH_INFO':'/test_redirect'
        }
        r = app(env, start_response)
        self.assertEqual(app._response.status, '302 Found')

    def test_handle_static(self):
        env = {
            'HTTP_HOST': 'localhost',
            'wsgi.url_scheme':'http' ,
            'SERVER_PORT':'80',
            'PATH_INFO':'/static/style.css'
        }
        r = app(env, start_response)
        self.assertEqual(app._response.status, '200 OK')
        self.assertEqual(app._response.content_type, 'text/css')

    def test_handle_static_not_found(self):
        env = {
            'HTTP_HOST': 'localhost',
            'wsgi.url_scheme':'http' ,
            'SERVER_PORT':'80',
            'PATH_INFO':'/static/main.css'
        }
        r = app(env, start_response)
        self.assertEqual(app._response.status, '404 Not Found')