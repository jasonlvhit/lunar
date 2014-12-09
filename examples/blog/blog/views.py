from . import *

@app.route('/')
def index():
    return app.render_template('index.html')


