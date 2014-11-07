from datetime import datetime
import unittest
import sqlite3

import database


class Post(database.Model):
    __tablename__ = 'post'

    id = database.PrimaryKeyField()
    title = database.CharField(100)
    content = database.TextField()
    pub_date = database.DateField()

    author_id = database.ForeignKeyField('author')

    def __repr__(self):
        return '<Post %s>' % self.title


class Author(database.Model):
    id = database.PrimaryKeyField()
    name = database.CharField(100)

    posts = database.ForeignKeyReverseField(Post)

    def __repr__(self):
        return '<Author %s>' % self.name


def get_connection():
    pass


class BaseTests(unittest.TestCase):

    def test_add(self):
        post = Post(title="My first post.",
                    content="Test my first post", pub_date=datetime.now())
        database.db.add(post)
        database.db.commit()

    def test_get(self):
        p1 = Post.get(id=1)
        p2 = Post.get(id=1, content="hello")

    def test_select(self):
        p1 = Post.select('*').where(id=2).all()
        p2 = Post.select().where("id > 0").all()
        p3 = Post.select().first()

    def test_delete(self):
        p = Post.delete(id=1).commit()
        p = Post.delete('id > 0').commit()

    def test_update(self):
        p = Post.update(id=1).set(title="new title").commit()
        p = Post.update("id > 2").set(
            title="new title", content="new content").commit()

    def test_foreignkeyfields(self):
        posts = Author.select().first().posts.all()

if __name__ == '__main__':
    pass
