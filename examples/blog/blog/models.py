from pumpkin import database

class Post_Tag_Re(database.Model):
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

    tags = database.ManyToManyField(rel='post_tag_re', to_table='tag')

    def __repr__(self):
        return '<Post %s>' % self.title


class Tag(database.Model):
    id = database.PrimaryKeyField()
    name = database.CharField(100)

    posts = database.ManyToManyField(rel='post_tag_re', to_table='post')

    def __repr__(self):
        return '<Tag %s>' % self.name

