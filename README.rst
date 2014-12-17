lunar
========

A WSGI based webframework.

.. image:: https://cloud.githubusercontent.com/assets/5202391/5469319/20677e82-8615-11e4-9aed-7773f47f7aea.jpg

What is Lunar?
----------------

Lunar是一个玩具式的网络框架，基于PEP333和它的进化版PEP3333，它包括

*  一个模板引擎: https://github.com/jasonlvhit/lunar/blob/master/lunar/template.py
*  一个Sqlite的ORM框架: https://github.com/jasonlvhit/lunar/blob/master/lunar/database.py
*  一个Router，用于请求转发和路由: https://github.com/jasonlvhit/lunar/blob/master/lunar/router.py
*  一个简单的对Request和Response对象的封装

查看example来看看这是怎么运作的。

lunar is a WSGI based webframework in pure Python, without any third-party dependency. 
lunar include a simple router, which provide the request routing, a template engine 
for template rendering, a simple wrapper for WSGI request and response, and a ORM framework 
for sqlite.

Happy hacking.

::

	from lunar.lunar import Lunar

	@app.route('/', methods = ["GET", "POST"])
	def hello():
		return "Hello, lunar!"

	if __name__ == '__main__':
		app.run()



