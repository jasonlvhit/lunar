# -*- coding: utf-8 -*-
""" A lightweight orm framework for sqlite.
	
"""
import os
import re
import sqlite3

PUMPKIN_CONFIG = {}
PUMPKIN_CONFIG.setdefault(
    'DATABASE_NAME', os.environ.get('PUMPKIN_DATABASE', 'pumpkin.db'))


class Database(object):
    pass


class DatabaseException(Exception):
    pass


class Sqlite(Database):

    def __init__(self, database):
        self.database = database
        self.conn = sqlite3.connect(
            self.database, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)

        self.__tabledict__ = {}

    def create_all(self):
        pass

    def create_table(self, model):
        c = []
        for field in model.__fields__.values():
            c.append(field.sql)
        cursor = self.conn.cursor()
        cursor.execute(
            'CREATE TABLE %s (%s);' % (model.__tablename__, ', '.join(c))
        )
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
            cofk.append(k)
            cofv.append('"' + str(v) + '"')

        cursor = self.conn.cursor()
        cursor.execute(
            'INSERT INTO %s (%s) values (%s);' % (instance.__class__.__tablename__,
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

db = Sqlite(PUMPKIN_CONFIG['DATABASE_NAME'])


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

    """ 
        trackId Integer NOT NULL REFERENCES "artist" ("id")
    """

    def __init__(self, to_table):
        """
        try:
                self.to_class = db.__tabledict__[to_table]
        except KeyError:
                raise DatabaseException('Referenced table did not exsited.')
        """
        self.to_table = to_table

    @property
    def sql(self):
        return '%s %s NOT NULL REFERENCES "%s" ("%s")' % (
            self.name, 'INTEGER', self.to_table, 'id'
        )


class ForeignKeyReverseField(object):

    def __init__(self, from_table):
        self.name = None
        self.tablename = None
        self.from_table = from_table
        self.id = None

    def update(self, name, tablename):
        self.name = name
        self.tablename = tablename
        self.from_class = db.__tabledict__[self.from_table]
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

    def update(self, name, tablename):
        self.name = name
        self.tablename = tablename

    def all(self):
        rel_class = db.__tabledict__[self.rel]
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
        c = db.execute(
            'select "%s" from %s where %s = "%s";' % (
                rel_id, self.rel, self_id, self.id)
        )
        rs = c.fetchall()
        return db.__tabledict__[self.to_table].select().where(
            ' or '.join(['id = "%s"' % c[0] for c in rs])
        ).all()

    def append(self, ins):
        pass

    def remove(self, *args, **kwargs):
        pass


class BaseModel(type):

    def __new__(cls, name, bases, attrs):
        cls = super(BaseModel, cls).__new__(cls, name, bases, attrs)
        # fields
        fields = {}
        refed_fields = {}
        cls_dict = cls.__dict__
        if '__tablename__' in cls_dict.keys():
            setattr(cls, '__tablename__', cls_dict['__tablename__'])
        else:
            setattr(cls, '__tablename__', cls.__name__.lower())

        db.__tabledict__[cls.__tablename__] = cls

        has_primary_key = False
        setattr(cls, 'has_relationship', False)
        for name, attr in cls.__dict__.items():
            if isinstance(attr, ForeignKeyReverseField) or isinstance(attr, ManyToManyField):
                setattr(cls, 'has_relationship', True)
                attr.update(name, cls.__tablename__)
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


class Model(metaclass=BaseModel):
    __metaclass__ = BaseModel

    def __init__(self, *args, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    @classmethod
    def get(cls, *args, **kwargs):
        return SelectQuery(cls, args).where(**kwargs).all()

    @classmethod
    def select(cls, *args):
        return SelectQuery(cls, args)

    @classmethod
    def update(cls, *args, **kwargs):
        return UpdateQuery(cls, args, **kwargs)

    @classmethod
    def delete(cls, *args, **kwargs):
        return DeleteQuery(cls, args, **kwargs)


class BaseQuery(object):
    base_statement = ''

    @property
    def sql(self):
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

    @property
    def sql(self):
        return self.base_statement % (', '.join([str(i).strip('\'').strip('"')
                                                 for i in self.query]).strip(','), self.klass.__tablename__)

    def _make_instance(self, descriptor, r):
        ins = self.klass(**dict(zip(descriptor, r)))
        for _, rf in ins.__refed_fields__.items():
            rf.id = ins.id

        return ins

    def all(self):
        c = db.execute(self.sql)
        descriptor = list(i[0] for i in c.description)
        rs = c.fetchall()
        ins_list = [self._make_instance(descriptor, r) for r in rs]
        return ins_list

    def first(self):
        c = db.execute(self.sql)
        rs = c.fetchone()
        return self._make_instance(list(i[0] for i in c.description), rs)

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
        c = db.execute(sql)
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

    def join(self):
        pass

    def having(self):
        pass

    def groupby(self):
        pass

    def orderby(self, asc=True):
        pass

    def like(self):
        pass


class UpdateQuery(BaseQuery):

    """ update post set title = "new title", content = "new content" 
            where id = 1;
    """

    def __init__(self, klass, *args, **kwargs):
        self.klass = klass
        self.base_statement = "update %s set %s;"
        self.where = None
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
        c = db.execute(self.sql, commit=True)
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
        c = db.execute(self.sql, commit=True)
        return c
