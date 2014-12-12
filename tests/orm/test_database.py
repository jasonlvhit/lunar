from datetime import datetime
import unittest

from pumpkin import database
from .models import Post_Tag_Re, Post, Author, Tag


def get_cursor():
    return database.db.conn.cursor()


def setup_database():
    database.db.create_table(Author)
    database.db.create_table(Post)
    database.db.create_table(Tag)
    database.db.create_table(Post_Tag_Re)

    for i in range(1, 6):
        get_cursor().execute('insert into author(name) values("test author ' + str(i) + '");')

    for i in range(1, 6):
        get_cursor().execute(
            'insert into self_define_post(title, content, author_id) values("test title %s", "test content %s", %s);' % (
                str(i), str(i), str(i)))

    for i in range(1, 6):
        get_cursor().execute('insert into tag(name) values("test tag ' + str(i) + '");')


def teardown_database():
    database.db.drop_table(Author)
    database.db.drop_table(Post)
    database.db.drop_table(Tag)
    database.db.drop_table(Post_Tag_Re)


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
            'newbase': database.MetaModel('NewBase', (object, ), {}),
            'tag': Tag,
            'post_tag_re': Post_Tag_Re,
            'model': database.Model,
            'self_define_post': Post,
        }

        self.assertEqual(init_dict, database.db.__tabledict__)


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
        self.assertEqual(Post.__refed_fields__.keys(), post_refed_fields)
        self.assertEqual(Tag.__refed_fields__.keys(), tag_refed_fields)

    def test_relationship(self):
        pass


class QueryTests(BaseTests):

    def test_add(self):
        author = Author(name='test author 6')
        database.db.add(author)
        database.db.commit()
        post = Post(title='test title 6', content='test content 6', author_id='6', pub_date=datetime.now())
        database.db.add(post)
        database.db.commit()
        c = database.db.execute('select * from author;')
        self.assertEqual(len(c.fetchall()), 6)
        c = database.db.execute('select * from self_define_post;')
        self.assertEqual(len(c.fetchall()), 6)

    def test_get(self):
        p1 = Post.get(id=1)[0]
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
        p2 = Post.get(id=5)[0]
        self.assertEqual(p2.title, 'new title 5')
        p3 = Post.update(id=-1).set(title="unexisted id").commit()
        self.assertEqual(p3.rowcount, 0)

    def test_foreignkeyfields(self):
        posts = Author.get(id=5)[0].posts.all()
        self.assertEqual(len(posts), 1)
        self.assertEqual(posts[0].id, 5)

    def test_many_to_many(self):
        posts = Tag.select().first().posts.all()
        tags = Post.select().first().tags.all()


    def test_mtom_append(self):
        p = Post.get(id=1)[0]
        p.tags.append(Tag.select().first())

    def test_mtom_remove(self):
        pass

    def test_mtom_count(self):
        pass

    def test_orderby(self):
        pass

    def test_like(self):
        pass


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
