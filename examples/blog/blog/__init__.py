from lunar import lunar
from lunar import database

app = lunar.Lunar('blog')
app.config['DATABASE_NAME'] = 'blog.db'

db = database.Sqlite(app.config['DATABASE_NAME'])

from . import views
