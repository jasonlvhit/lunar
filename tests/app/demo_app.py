from pumpkin.pumpkin import Pumpkin

app = Pumpkin('__main__')

@app.route('/', methods=["GET", "POST"])
def index():
    return "Hello, Pumpkin!"

#/args?key=pumpkin&count=4
@app.route('/test_args', methods=["GET"])
def test_args():
    return app.request.args["key"], app.request.args["count"]

@app.route('/show/<int:id>')
def test_sync_args(id):
    return id
    
# template
@app.route('/template')
def template():
    return app.render_template('index.html')

@app.route('/url_for_with_args')
def test_url_for_with_args():
    return app.url_for(test_sync_args, id=1)

@app.route('/url_for_static')
def test_url_for():
    return app.url_for('static', 'style.css')

@app.route('/push_session')
def push_session():
    app.session['pumpkin'] = "a web framework"
    return app.session['pumpkin'].value

@app.route('/show_session')
def show_session():
    return app.session['pumpkin'].value

@app.route('/test_redirect')
def test_redirect():
    return app.redirect('/')

@app.route('/redirect_with_args')
def test_redirect_with_url():
    return app.redirect(app.url_for(test_sync_args, id=1))

if __name__ == '__main__':
    app.run(DEBUG=True)
