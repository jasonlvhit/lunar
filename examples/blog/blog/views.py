from datetime import datetime
from .models import Post, Tag
from . import app, db

@app.route('/')
def index():
    return app.render_template('index.html')


def tag_filter(tags):
    l = tags.strip().split(' ')
    existed_tags = Tag.select().all()
    s = set([i.name for i in existed_tags])
    for i in l:
        if i not in s:
            db.add(Tag(name=i))
            db.commit()
    return [i for i in existed_tags if i.tag_name in set(l)]


@app.route('/new_post', methods=['POST', 'GET'])
def create_post():
    if app.request.method == 'GET':
        return app.render_template("editor.html")

    title = app.request.form['title']
    tags = tag_filter(app.request.form['tag'])
    content = app.request.form['editor']
    post = Post(title=title, content=content, pub_date=datetime.now())
    for i in tags:
        post.tag.append(i)
    db.add(post)
    db.commit()
    return app.redirect(app.url_for(show_post, id=post.id))

@app.route('/post/<int:id>')
def show_post(id):
    return id