from datetime import datetime
from . import app, db
from .models import Comment, Post, Tag
from .renderer import md_renderer

@app.route('/')
def index():
    posts = Post.select().all()
    return app.render('index.html', posts=posts)


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
        return app.render("editor.html")

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
    p = Post.get(id=id)
    p.content = md_renderer.render(p.content)
    return app.render('post.html', post=p)

@app.route('/tag/<int:id>')
def show_tag(id):
    t = Tag.get(id=id)
    return app.render('tag.html', tag=t)

@app.route('/new_comment', methods=['POST'])
def create_comment():
    post_id = app.request.forms['post_id']
    title = app.request.forms['title']
    content = app.request.forms['content']
    comment = Comment(title=title, content=content, pub_date=datetime.now(), post_id=post_id)
    db.add(comment)
    db.commit()
    return app.redirect(app.url_for(show_post, id=post_id))


