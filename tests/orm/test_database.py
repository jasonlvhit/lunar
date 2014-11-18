from datetime import datetime
import unittest
import sqlite3

import database

class Post_Tag_Re(database.Model):
    """
    Many to many relationship test.
    """
    id = database.PrimaryKeyField()
    post_id = database.ForeignKeyField('self_define_post')
    tag_id = database.ForeignKeyField('tag')

    def __repr__(self):
        return '<Relation table post_id = %s, tag_id = %s>' %(
            post_id, tag_id
            )


class Post(database.Model):
    __tablename__ = 'self_define_post'

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

    posts = database.ForeignKeyReverseField('self_define_post')

    def __repr__(self):
        return '<Author %s>' % self.name

class Tag(database.Model):
    id = database.PrimaryKeyField()
    name = database.CharField(100)

    posts = database.ManyToManyField(rel = 'post_tag_re', to_table = 'self_define_post')

    def __repr__(self):
        return '<Tag %s>' % self.name


def get_cursor():
    return database.db.conn.cursor()

def setup():
    database.db.create_table(Author)
    database.db.create_table(Post)
    database.db.create_table(Tag)
    database.db.create_table(Post_Tag_Re)

    for i in range(0, 5):
        get_cursor().execute('insert into author(name) values("test author ' + str(i) +'");')

    for i in range(0, 5):
        get_cursor().execute('insert into self_define_post(title, content, author_id) values("test title %s", "test content %s", %s);' % (str(i), str(i), str(i)))
        
    for i in range(0, 5):
        get_cursor().execute('insert into tag(name) ')

class BaseTests(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_create_table(self):
        pass

    def test_drop_table(self):
        pass

    def test_roll_back(self):
        pass

    def test_close(self):
        pass

    def test_execute(self):
        pass

    def test_commit(self):
        pass

    def test_init(self):
        init_dict = {
        'author': <class 'test_database.Author'>, 
        'newbase': <class 'database.NewBase'>, 
        'tag': <class 'test_database.Tag'>, 
        'post_tag_re': <class 'test_database.Post_Tag_Re'>, 
        'model': <class 'database.Model'>, 
        'self_define_post': <class 'test_database.Post'>,
        }

        self.assertEqual(init_dict, database.db.__tabledict__)


class ModelTests(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_self_define_tablename(self):
        self.assertEqual(Post.__tablename__, 'self_define_post')

    def test_default_tablename(self):
        self.assertEqual(Author.__tablename__, 'author')

    def test_fields(self):
        post_fields = {
        'pub_date': <database.DateField object at 0x0000000002A98BA8>, 
        'title': <database.CharField object at 0x0000000002A98630>, 
        'author_id': <database.ForeignKeyField object at 0x0000000002A9F358>, 
        'id': <database.PrimaryKeyField object at 0x0000000002B5CB70>, 
        'content': <database.TextField object at 0x0000000002A988D0>
        }
        self.assertEqual(post_fields.keys(), Post.__fields__.keys())

    def test_refed_fields(self):
        post_refed_fields = ['tags']
        tag_refed_fields = ['posts']
        self.assertEqual(Post.__refed_fields__.keys(), post_refed_fields)
        self.assertEqual(Tag.__refed_fields__.keys(), tag_refed_fields)

    def test_relationship(self):
        pass
        

class QueryTests(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_add(self):
        for i in range(0, 5):
            p = Post(title = "test post " + str(i), content = "test content " + str(i))

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

    def setUp(self):
        pass

    def tearDown(self):
        pass

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
