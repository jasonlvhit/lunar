from lunar import Lunar
from lunar import database

app = Lunar('blog')
app.config['DATABASE_NAME'] = 'blog.db'

db = database.Sqlite(app.config['DATABASE_NAME'])

from . import views
