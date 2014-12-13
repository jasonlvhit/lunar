from pumpkin import pumpkin

app = pumpkin.Pumpkin('blog')
app.config['DATABASE_NAME'] = 'blog.db'

from . import views
