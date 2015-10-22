from lunar import Lunar

app = Lunar('__main__')


@app.route('/', methods=["GET", "POST"])
def index():
    return "Hello, lunar!"


#/args?key=lunar&count=4
@app.route('/test_args', methods=["GET"])
def test_args():
    return app.request.args["key"], app.request.args["count"]

# template


@app.route('/template')
def template():
    return app.render('index.html')


@app.route('/template_with_noescape')
def test_escape():
    return app.render('test_escape.html', content="<p>hello escape</p>")


@app.route('/url_for_with_args')
def test_url_for_with_args():
    return app.url_for(test_sync_args, id=1)


@app.route('/url_for')
def test_url_for():
    return app.url_for(index)


@app.route('/push_session')
def push_session():
    app.session['lunar'] = "a web framework"
    return app.session['lunar'].value


@app.route('/show_session')
def show_session():
    return app.session['lunar'].value


@app.route('/show/<int:id>')
def test_sync_args(id):
    return id


@app.route('/test_post', methods=['GET', 'POST'])
def test_post():
    if app.request.method == 'GET':
        return app.render('test_post.html')
    return app.request.form["title"], app.request.form["tag"]


@app.route('/test_redirect')
def test_redirect():
    return app.redirect('/')


@app.route('/redirect_with_args')
def test_redirect_with_url():
    return app.redirect(app.url_for(test_sync_args, id=1))


@app.route('/test_jsonify')
def test_jsonify():
    return app.jsonify(name='lunar')


if __name__ == '__main__':
    app.run(debug=True)
