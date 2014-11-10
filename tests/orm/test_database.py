from datetime import datetime
import unittest
import sqlite3

import database

class Post_Tag_Re(database.Model):
    """
    Many to many relationship test.
    """
    id = database.PrimaryKeyField()
    post_id = database.ForeignKeyField('post')
    tag_id = database.ForeignKeyField('tag')

    def __repr__(self):
        return '<Relation table post_id = %s, tag_id = %s>' %(
            post_id, tag_id
            )


class Post(database.Model):
    __tablename__ = 'post'

    id = database.PrimaryKeyField()
    title = database.CharField(100)
    content = database.TextField()
    pub_date = database.DateField()

    author_id = database.ForeignKeyField('author')
    tags = database.ManyToManyField(rel = 'post_tag_re', to_table = 'tag')

    def __repr__(self):
        return '<Post %s>' % self.title


class Author(database.Model):
    id = database.PrimaryKeyField()
    name = database.CharField(100)

    posts = database.ForeignKeyReverseField('post')

    def __repr__(self):
        return '<Author %s>' % self.name

class Tag(database.Model):
    id = database.PrimaryKeyField()
    name = database.CharField(100)

    posts = database.ManyToManyField(rel = 'post_tag_re', to_table = 'post')

    def __repr__(self):
        return '<Tag %s>' % self.name


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

    def test_many_to_many(self):
        posts = Tag.select().first().posts.all()
        tags = Post.select().first().tags.all()

    
    def test_mtom_append(self):
        p = Post.get(id = 1)[0]
        p.tags.append(Tag.select().first())

    def test_mtom_remove(self):
        pass

    def test_mtom_count(self):
        pass

    def test_orderby(self):
        pass

    def test_like(self):
        pass


class TestBasicFunction(unittest.TestCase):

    def test_count(self):
        c1 = Post.select().count()
        c2 = Post.select().where("id > 3").count()

    def test_max(self):
        pass

    def test_min(self):
        pass

    def test_avg(self):
        pass

    def test_sum(self):
        pass

if __name__ == '__main__':
    pass
