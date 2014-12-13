from datetime import datetime
from .models import Post, Tag
from pumpkin.database import db
from . import app

@app.route('/')
def index():
    posts = Post.select().all()
    return app.render_template('index.html', posts=posts)


def tag_filter(tags):
    l = tags.strip().split(' ')
    existed_tags = Tag.select().all()
    s = set([i.name for i in existed_tags])
    for i in l:
        if i not in s:
            db.add(Tag(name=i))
            db.commit()
    return [i for i in Tag.select().all() if i.name in set(l)]


@app.route('/new_post', methods=['POST', 'GET'])
def create_post():
    if app.request.method == 'GET':
        return app.render_template("editor.html")

    title = app.request.forms['title']
    tags = tag_filter(app.request.forms['tag'])
    content = app.request.forms['editor']
    post = Post(title=title, content=content, pub_date=datetime.now())
    db.add(post)
    db.commit()
    for i in tags:
        post.tags.append(i)
    return app.redirect(app.url_for(show_post, id=post.id))

@app.route('/post/<int:id>')
def show_post(id):
    p = Post.get(id=id)[0]
    return app.render_template('post.html', post=p)