from lunar import database
from . import db

class Post_Tag_Re(db.Model):
    id = database.PrimaryKeyField()
    post_id = database.ForeignKeyField('post')
    tag_id = database.ForeignKeyField('tag')

    def __repr__(self):
        return '<Relation table post_id = %s, tag_id = %s>' %(
            self.post_id, self.tag_id
            )


class Comment(db.Model):
    id = database.PrimaryKeyField()
    title = database.CharField(100)
    content = database.CharField(400)
    pub_date = database.DateField()

    post_id = database.ForeignKeyField('post')

    def __repr__(self):
        return '<Comment %s>' % self.title


class Post(db.Model):
    __tablename__ = 'post'

    id = database.PrimaryKeyField()
    title = database.CharField(100)
    content = database.TextField()
    pub_date = database.DateField()

    tags = database.ManyToManyField(rel='post_tag_re', to_table='tag')
    comments = database.ForeignKeyReverseField('comment')

    def __repr__(self):
        return '<Post %s>' % self.title


class Tag(db.Model):
    id = database.PrimaryKeyField()
    name = database.CharField(100)

    posts = database.ManyToManyField(rel='post_tag_re', to_table='post')

    def __repr__(self):
        return '<Tag %s>' % self.name

