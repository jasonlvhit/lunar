from pumpkin import pumpkin
from pumpkin import database

app = pumpkin.Pumpkin('blog')
app.config['DATABASE_NAME'] = 'blog.db'

db = database.Sqlite(app.config['DATABASE_NAME'])

from . import views
