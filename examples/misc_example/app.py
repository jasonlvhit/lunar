from pumpkin.pumpkin import Pumpkin

app = Pumpkin('__main__')


@app.route('/', methods=["GET", "POST"])
def hello():
    return "Hello, Pumpkin!"


#/args?key=pumpkin&count=4
@app.route('/args', methods=["GET"])
def args():
    return (app.request.args["key"], app.request.args["count"])

# template


@app.route('/template')
def template():
    return app.render_template('index.html')


@app.route('/template_with_noescape')
def test_escape():
    return app.render_template('test_escape.html', content="<p>hello escape</p>")

# url_for


@app.route('/url_for')
def test_url_for():
    return app.url_for(hello)


@app.route('/session')
def push_session():
    app.session['pumpkin'] = "a web framework"
    return app.session['pumpkin'].value


@app.route('/show_session')
def show_session():
    return app.session['pumpkin'].value


@app.route('/show/<int:id>')
def test_sync_args(id):
    return id


@app.route('/test_post', methods=['GET', 'POST'])
def test_post():
    if app.request.method == 'GET':
        return app.render_template('test_post.html')
    return (app.request.forms["title"], app.request.forms["tag"])


@app.route('/test_redirect')
def test_redirect():
    return app.redirect('/')

if __name__ == '__main__':
    app.run()
