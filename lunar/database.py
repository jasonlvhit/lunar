# -*- coding: utf-8 -*-
""" A lightweight orm framework for sqlite.
    
"""
import copy
import sqlite3
import sys
import threading

from .util import sqlite_escape

encoding_type = 'utf8'


def u(r):
    def f(x):
        if sys.version < '3' and isinstance(x, unicode):
            return x.encode(encoding_type)
        return x

    return list(map(f, r))


class Field(object):
    name = ''

    @property
    def sql(self):
        pass


class IntegerField(Field):

    @property
    def sql(self):
        return '"%s" %s' % (self.name, "INTEGER")


class CharField(Field):

    def __init__(self, max_length=255):
        self.max_length = max_length

    @property
    def sql(self):
        return '%s %s(%d) NOT NULL' % (self.name, "VARCAHR", self.max_length)


class TextField(Field):

    @property
    def sql(self):
        return '"%s" %s' % (self.name, "TEXT")


class RealField(Field):

    @property
    def sql(self):
        return '"%s" %s' % (self.name, "REAL")


class DateField(Field):

    @property
    def sql(self):
        return '"%s" %s' % (self.name, "DATETIME")


class PrimaryKeyField(IntegerField):

    @property
    def sql(self):
        return '"%s" %s NOT NULL PRIMARY KEY' % (self.name, "INTEGER")


class ForeignKeyField(IntegerField):

    def __init__(self, to_table):
        self.to_table = to_table

    @property
    def sql(self):
        return '%s %s NOT NULL REFERENCES "%s" ("%s")' % (
            self.name, 'INTEGER', self.to_table, 'id'
        )


class ForeignKeyReverseField(object):

    def __init__(self, from_table):
        self.from_table = from_table
        self.name = None
        self.tablename = None
        self.id = None
        self.db = None
        self.from_class = None
        self.re = None

    def update(self, name, tablename, db):
        self.name = name
        self.tablename = tablename
        self.db = db
        self.from_class = self.db.__tabledict__[self.from_table]
        for name, attr in self.from_class.__dict__.items():
            if isinstance(attr, ForeignKeyField) and attr.to_table == self.tablename:
                self.re = name

    def all(self):
        return self.from_class.select('*').where('='.join([self.re, str(self.id)])).all()

    def count(self):
        return self.from_class.select('*').where('='.join([self.re, str(self.id)])).count()


class ManyToManyField(object):

    def __init__(self, rel=None, to_table=None):
        if not rel or not to_table:
            raise DatabaseException(
                "Many to many fields must set a rel table.")
        self.rel = rel
        self.to_table = to_table
        self.id = None
        self.self_id = None
        self.db = None
        self.name = None

    def update(self, name, tablename, db):
        self.name = name
        self.tablename = tablename
        self.db = db

    def _get_rel_names(self):
        rel_class = self.db.__tabledict__[self.rel]
        self_id = None
        rel_id = None
        for name, field in rel_class.__fields__.items():
            if isinstance(field, ForeignKeyField):
                if field.to_table == self.tablename:
                    self_id = name
                elif field.to_table == self.to_table:
                    rel_id = name
        if not self_id or not rel_id:
            raise DatabaseException("No matched fields in relation table.")
        return self_id, rel_id

    def _select(self):
        self_id, rel_id = self._get_rel_names()
        c = self.db.execute(
            'select %s from %s where %s = %s;' % (
                rel_id, self.rel, self_id, self.id)
        )
        rs = c.fetchall()
        if len(rs) == 0:
            return self.db.__tabledict__[self.to_table].select().where('id=-1')
        return self.db.__tabledict__[self.to_table].select().where(
            ' or '.join(['id = "%s"' % c[0] for c in rs])
        )

    def all(self):
        return self._select().all()

    def append(self, ins):
        """
        p.tags.append(tag_instance)
        -->
        insert into rel_table(self_id, rel_id) values(self.id, ins.id);
        """
        self_id, rel_id = self._get_rel_names()
        c = self.db.execute(
            'insert into %s(%s, %s) values(%s, %s);' % (
                self.rel, self_id, rel_id, self.id, ins.id
            ), commit=True
        )
        return c

    def remove(self, *args):
        """
        p.tags.remove("tag_id = 1")
        -->
        delete from rel_table where self_id = self.id and tag_id = 1;
        """
        if not self.self_id:
            self.self_id, _ = self._get_rel_names()
        c = self.db.execute(
            'delete from %s where %s = %s and %s;' % (
                self.rel, self.self_id, self.id,
                ' and '.join(list(args))
            ), commit=True
        )
        return c

    def count(self):
        return self._select().count()


class MetaModel(type):

    def __new__(cls, name, bases, attrs):
        cls = super(MetaModel, cls).__new__(cls, name, bases, attrs)
        # fields
        fields = {}
        refed_fields = {}
        cls_dict = cls.__dict__
        if '__tablename__' in cls_dict.keys():
            setattr(cls, '__tablename__', cls_dict['__tablename__'])
        else:
            setattr(cls, '__tablename__', cls.__name__.lower())

        if hasattr(cls, 'db'):
            getattr(cls, 'db').__tabledict__[cls.__tablename__] = cls

        has_primary_key = False
        setattr(cls, 'has_relationship', False)
        for name, attr in cls.__dict__.items():
            if isinstance(attr, ForeignKeyReverseField) or isinstance(attr, ManyToManyField):
                setattr(cls, 'has_relationship', True)
                attr.update(name, cls.__tablename__, cls.db)
                refed_fields[name] = attr
            if isinstance(attr, Field):
                attr.name = name
                fields[name] = attr
                if isinstance(attr, PrimaryKeyField):
                    has_primary_key = True

        if not has_primary_key:
            pk = PrimaryKeyField()
            pk.name = 'id'
            fields['id'] = pk
        setattr(cls, '__fields__', fields)
        setattr(cls, '__refed_fields__', refed_fields)
        return cls


class Model(MetaModel('NewBase', (object, ), {})):

    def __init__(self, **kwargs):
        max_id = self.select('id').max()
        if not max_id:
            max_id = 0
        self.id = max_id + 1

        for k, v in self.__refed_fields__.items():
            if isinstance(v, ForeignKeyReverseField) or isinstance(v, ManyToManyField):
                v.id = self.id
                t = copy.deepcopy(v)
                setattr(t, 'db', v.db)
                setattr(self, k, t)

        for k, v in kwargs.items():
            setattr(self, k, v)

    @classmethod
    def get(cls, *args, **kwargs):
        # get method only supposes to be used by querying by id.
        # UserModel.get(id=2)
        # return a single instance.
        return SelectQuery(cls, args).where(**kwargs).first()

    @classmethod
    def select(cls, *args):
        return SelectQuery(cls, args)

    @classmethod
    def update(cls, *args, **kwargs):
        return UpdateQuery(cls, args, **kwargs)

    @classmethod
    def delete(cls, *args, **kwargs):
        return DeleteQuery(cls, args, **kwargs)


class Database(threading.local):
    pass


class DatabaseException(Exception):
    pass


class Sqlite(Database):

    def __init__(self, database):
        self.database = database
        self.conn = sqlite3.connect(
            self.database, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)

        self.__tabledict__ = {}
        self.__db__ = self
        setattr(self, 'Model', Model)
        c = getattr(self, 'Model')
        if hasattr(self, '__db__'):
            setattr(c, 'db', getattr(self, '__db__'))

    def create_all(self):
        for k, v in self.__tabledict__.items():
            if issubclass(v, self.Model):
                print("create table %s..." % k)
                self.create_table(v)

    def create_table(self, model):
        c = []
        for field in model.__fields__.values():
            c.append(field.sql)
        cursor = self.conn.cursor()
        cursor.execute(
            'create table %s (%s);' % (model.__tablename__, ', '.join(c))
        )
        if not model.__tablename__ in self.__tabledict__.keys():
            self.__tabledict__[model.__tablename__] = model

        self.commit()

    def drop_table(self, model):
        cursor = self.conn.cursor()
        cursor.execute('drop table %s;' % model.__tablename__)
        del self.__tabledict__[model.__tablename__]
        self.commit()

    def add(self, instance):
        """ insert into post(title, content, pub_date) 
                values ("title", "content", datetime.datetime.now())
        """
        cofk = []
        cofv = []
        for k, v in instance.__dict__.items():
            if isinstance(v, ManyToManyField) or isinstance(v, ForeignKeyReverseField):
                continue
            cofk.append(k)
            cofv.append('\'' + sqlite_escape(str(v)) + '\'')

        cursor = self.conn.cursor()
        cursor.execute(
            'insert into %s (%s) values (%s);' % (instance.__class__.__tablename__,
                                                  ', '.join(cofk), ', '.join(cofv))
        )
        return cursor

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()

    def close(self):
        self.conn.close()

    def execute(self, sql, commit=False):
        cursor = self.conn.cursor()
        cursor.execute(sql)
        if commit:
            self.commit()
        return cursor


class BaseQuery(object):
    base_statement = ''

    @property
    def sql(self):
        pass


class QueryException(DatabaseException):
    pass


class SelectQuery(BaseQuery):

    """ select title, content from post where id = 1 and title = "my title";
        select title, content from post where id > 3;
    """

    def __init__(self, klass, *args):
        self.base_statement = 'select %s from %s;'
        self.klass = klass
        self.query = ['*']
        if args != ((), ):
            self.query = list(*args)
        self.like_pattern = None

    @property
    def sql(self):
        if self.like_pattern:
            return self.base_statement % (
                ', '.join([str(i).strip('\'').strip('"')
                           for i in self.query]).strip(','), self.klass.__tablename__, self.like_pattern
            )
        return self.base_statement % (
            ', '.join([str(i).strip('\'').strip('"')
                       for i in self.query]).strip(','), self.klass.__tablename__
        )

    def _make_instance(self, descriptor, r):
        # must handle empty case.
        try:
            ins = self.klass(**dict(zip(descriptor, r)))
        except TypeError:
            return None
        for _, rf in ins.__dict__.items():
            if isinstance(rf, ManyToManyField) or isinstance(rf, ForeignKeyReverseField):
                rf.id = ins.id
        return ins

    def all(self):
        c = self.klass.db.execute(self.sql)
        descriptor = list(i[0] for i in c.description)
        rs = c.fetchall()
        ins_list = [self._make_instance(descriptor, u(r)) for r in rs]
        return ins_list

    def first(self):
        c = self.klass.db.execute(self.sql)
        rs = c.fetchone()
        if not rs:
            return None
        return self._make_instance(list(i[0] for i in c.description), u(rs))

    def where(self, *args, **kwargs):
        c = ['%s = "%s"' % (k, str(v)) for k, v in kwargs.items()]
        if c != ((),):
            c.extend(list(args))
        self.base_statement = "select %s from %s where " + \
                              ' and '.join(c) + ";"
        return self

    def _base_function(self, func):
        sql = self.base_statement % (
            func + '("' + ', '.join([str(i).strip('\'').strip('"')
                                     for i in self.query]).strip(',') + '")', self.klass.__tablename__
        )
        c = self.klass.db.execute(sql)
        rs = c.fetchone()
        return rs[0]

    def count(self):
        return self._base_function('count')

    def max(self):
        """
        Post.select('id').max()
        """
        return self._base_function('max')

    def min(self):
        return self._base_function('min')

    def avg(self):
        return self._base_function('avg')

    def sum(self):
        return self._base_function('sum')

    def orderby(self, order=None, by='asc'):
        """
        test_database.Post.select().orderby('id', 'asc').all()
        """
        self.base_statement = ' '.join(
            [self.base_statement.strip(';'), 'order by', order, by, ';'])
        return self

    def like(self, pattern):
        """
        test_database.Post.select('id').where('content').like('%cont%')
        """
        if 'where' not in self.base_statement:
            raise QueryException("like query must have a where clause before.")
        self.like_pattern = pattern or ''
        self.base_statement = ''.join(
            [self.base_statement.strip(';'), ' like "%s";'])
        return self

    def notlike(self, pattern):
        """
        test_database.Post.select('id').where('content').notlike('%cont%')
        """
        if 'where' not in self.base_statement:
            raise QueryException("like query must have a where clause before.")
        self.like_pattern = pattern or ''
        self.base_statement = ''.join(
            [self.base_statement.strip(';'), ' not like "%s";'])
        return self


class UpdateQuery(BaseQuery):

    """ update post set title = "new title", content = "new content"
        where id = 1;
    """

    def __init__(self, klass, *args, **kwargs):
        self.klass = klass
        self.base_statement = "update %s set %s;"
        self.where = None
        self.update_value = None
        if args != ((),) or kwargs:
            c = ['%s = "%s"' % (k, str(v)) for k, v in kwargs.items()]
            if args != ((),):
                c.extend(list(*args))
            self.where = "where " + ' and '.join(c)

    @property
    def sql(self):
        if self.where:
            self.base_statement = ' '.join(
                ['update %s set %s', self.where, ';'])

        return self.base_statement % (self.klass.__tablename__, self.update_value)

    def set(self, *args, **kwargs):
        self.update_value = ' and '.join(
            ['"%s" = "%s"' % (k, v) for k, v in kwargs.items()])
        return self

    def commit(self):
        c = self.klass.db.execute(self.sql, commit=True)
        return c


class DeleteQuery(BaseQuery):

    def __init__(self, klass, *args, **kwargs):
        self.base_statement = 'delete from %s;'
        self.c = None
        if args != ((),) or kwargs:
            self.base_statement = 'delete from %s where %s;'
            self.c = ['%s = "%s"' % (k, str(v)) for k, v in kwargs.items()]
            if args != ((),):
                self.c.extend(list(*args))
        self.klass = klass

    @property
    def sql(self):
        if self.c:
            return self.base_statement % (self.klass.__tablename__, ' and '.join(self.c))
        return self.base_statement % self.klass.__tablename__

    def commit(self):
        c = self.klass.db.execute(self.sql, commit=True)
        return c
