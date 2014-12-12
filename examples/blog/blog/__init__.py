from pumpkin import pumpkin, database

app = pumpkin.Pumpkin('blog')
app.config['DATABASE_NAME'] = 'blog.db'

db = database.db

from . import views
