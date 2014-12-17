from datetime import datetime
import unittest

from lunar import database
from . import db
from .models import Post_Tag_Re, Post, Author, Tag


def get_cursor():
    return db.conn.cursor()


def setup_database():
    db.create_table(Author)
    db.create_table(Post)
    db.create_table(Tag)
    db.create_table(Post_Tag_Re)

    for i in range(1, 6):
        get_cursor().execute(
            'insert into author(name) values("test author ' + str(i) + '");')

    for i in range(1, 6):
        get_cursor().execute(
            'insert into self_define_post(title, content, author_id) values("test title %s", "test content %s", %s);' % (
                str(i), str(i), str(i)))

    for i in range(1, 6):
        get_cursor().execute(
            'insert into tag(name) values("test tag ' + str(i) + '");')


def teardown_database():
    db.drop_table(Author)
    db.drop_table(Post)
    db.drop_table(Tag)
    db.drop_table(Post_Tag_Re)


class BaseTests(unittest.TestCase):

    def setUp(self):
        setup_database()

    def tearDown(self):
        teardown_database()

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
            'author': Author,
            'tag': Tag,
            'post_tag_re': Post_Tag_Re,
            'self_define_post': Post,
        }

        self.assertEqual(init_dict, db.__tabledict__)


class ModelTests(BaseTests):

    def test_self_define_tablename(self):
        self.assertEqual(Post.__tablename__, 'self_define_post')

    def test_default_tablename(self):
        self.assertEqual(Author.__tablename__, 'author')

    def test_fields(self):
        post_fields = {
            'pub_date': database.DateField,
            'title': database.CharField,
            'author_id': database.ForeignKeyField,
            'id': database.PrimaryKeyField,
            'content': database.TextField
        }
        self.assertEqual(post_fields.keys(), Post.__fields__.keys())

    def test_refed_fields(self):
        post_refed_fields = ['tags']
        tag_refed_fields = ['posts']
        self.assertEqual(
            [i for i in Post.__refed_fields__.keys()], post_refed_fields)
        self.assertEqual(
            [i for i in Tag.__refed_fields__.keys()], tag_refed_fields)

    def test_relationship(self):
        pass


class QueryTests(BaseTests):

    def test_add(self):
        author = Author(name='test author 6')
        db.add(author)
        db.commit()
        post = Post(title='test title 6', content='test content 6',
                    author_id='6', pub_date=datetime.now())
        db.add(post)
        db.commit()
        c = db.execute('select * from author;')
        self.assertEqual(len(c.fetchall()), 6)
        c = db.execute('select * from self_define_post;')
        self.assertEqual(len(c.fetchall()), 6)

    def test_get(self):
        p1 = Post.get(id=1)
        self.assertEqual(p1.title, 'test title 1')
        self.assertEqual(p1.content, 'test content 1')
        self.assertEqual(p1.author_id, 1)

    def test_select(self):
        p1 = Post.select('*').where(id=2).all()
        self.assertEqual(len(p1), 1)
        self.assertEqual(p1[0].id, 2)
        p2 = Post.select().where("id < 5").all()
        self.assertEqual(len(p2), 4)
        self.assertEqual([1, 2, 3, 4], [i.id for i in p2])

        p3 = Post.select().first()
        self.assertEqual(p3.id, 1)

    def test_delete(self):
        p1 = Post.delete(id=1).commit()
        self.assertEqual(p1.rowcount, 1)
        p2 = Post.delete(id=1).commit()
        self.assertEqual(p2.rowcount, 0)

        p3 = Post.delete('id < 3').commit()
        self.assertEqual(p3.rowcount, 1)

    def test_update(self):
        p1 = Post.update(id=5).set(title="new title 5").commit()
        self.assertEqual(p1.rowcount, 1)
        p2 = Post.get(id=5)
        self.assertEqual(p2.title, 'new title 5')
        p3 = Post.update(id=-1).set(title="unexisted id").commit()
        self.assertEqual(p3.rowcount, 0)

    def test_foreignkeyfields(self):
        posts = Author.get(id=5).posts.all()
        self.assertEqual(len(posts), 1)
        self.assertEqual(posts[0].id, 5)

    def test_orderby(self):
        posts = Post.select().orderby('id', 'asc').all()
        self.assertEqual([p.id for p in posts], [1, 2, 3, 4, 5])
        posts = Post.select().orderby('id', 'desc').all()
        self.assertEqual([p.id for p in posts], [5, 4, 3, 2, 1])

    def test_like(self):
        posts = Post.select().where('content').like("test%").all()
        self.assertEqual([p.id for p in Post.select().all()], [i.id for i in posts])
        posts = Post.select().where('id').like("1").all()
        self.assertEqual([Post.get(id=1).id], [p.id for p in posts])
        posts = Post.select().where('content').like('%est%').all()
        self.assertEqual([p.id for p in Post.select().all()], [i.id for i in posts])


class ManytoManyFieldsTest(BaseTests):

    def test_mtom_append(self):
        p = Post.get(id=1)
        t1 = Tag.get(id=1)
        t2 = Tag.get(id=2)
        p.tags.append(t1)
        p.tags.append(t2)
        self.assertEqual([p.id for p in p.tags.all()], [t1.id, t2.id])
        self.assertEqual([p.id for p in t1.posts.all()], [p.id])
        self.assertEqual([p.id for p in t2.posts.all()], [p.id])

    def test_mtom_remove(self):
        p = Post.get(id=5)
        self.assertEqual(p.tags.all(), [])
        t = Tag.get(id=5)
        p.tags.append(t)
        self.assertEqual([t.id for t in p.tags.all()], [t.id])
        self.assertEqual([p.id for p in t.posts.all()], [p.id])
        p.tags.remove("tag_id=5")
        self.assertEqual(p.tags.all(), [])
        self.assertEqual(t.posts.all(), [])

    def test_mtom_count(self):
        p = Post.get(id=3)
        self.assertEqual(p.tags.count(), 0)
        p.tags.append(Tag.get(id=3))
        p.tags.append(Tag.get(id=4))
        self.assertEqual(p.tags.count(), 2)


class TestBasicFunction(BaseTests):

    def test_count(self):
        c1 = Post.select().count()
        self.assertEqual(c1, 5)
        c2 = Post.select().where("id > 3").count()
        self.assertEqual(c2, 2)

    def test_max(self):
        c1 = Post.select('id').max()
        self.assertEqual(c1, 5)
        c2 = Post.select('id').where('id < 3').max()
        self.assertEqual(c2, 2)
        c3 = Post.select('id').where('id > 10').max()
        self.assertEqual(c3, None)

    def test_min(self):
        c1 = Post.select('id').min()
        self.assertEqual(c1, 1)

    def test_avg(self):
        c1 = Post.select('id').avg()
        self.assertEqual(c1, 3)

    def test_sum(self):
        c1 = Post.select('id').sum()
        self.assertEqual(c1, 15)


if __name__ == '__main__':
    pass
