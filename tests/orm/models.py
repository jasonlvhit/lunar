from pumpkin import database

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
    tags = database.ManyToManyField(rel='post_tag_re', to_table='tag')

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

    posts = database.ManyToManyField(rel='post_tag_re', to_table='self_define_post')

    def __repr__(self):
        return '<Tag %s>' % self.name

