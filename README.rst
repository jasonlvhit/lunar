Pumpkin
========

A WSGI based webframework.


What is Pumpkin?
----------------

Pumpkin是一个玩具式的网络框架，基于PEP333和它的进化版PEP3333，它包括

*  一个模板引擎: https://github.com/jasonlvhit/pumpkin/blob/master/pumpkin/template.py
*  一个Sqlite的ORM框架: https://github.com/jasonlvhit/pumpkin/blob/master/pumpkin/database.py
*  一个Router，用于请求转发和路由: https://github.com/jasonlvhit/pumpkin/blob/master/pumpkin/router.py
*  一个简单的对Request和Response对象的封装

查看example来看看这是怎么运作的。

Pumpkin is a WSGI based webframework in pure Python, without any third-party dependency. 
Pumpkin include a simple router, which provide the request routing, a template engine 
for template rendering, a simple wrapper for WSGI request and response, and a orm framework 
for sqlite.

Happy hacking.

::

	from pumpkin.pumpkin import Pumpkin

	@app.route('/', methods = ["GET", "POST"])
	def hello():
		return "Hello, Pumpkin!"

	if __name__ == '__main__':
		app.run()



About Pumpkin
--------------

洋葱、萝卜和番茄不相信世界上有南瓜这个东西，它们认为那只是空想。南瓜默默不说话，它只是继续成长。
这句话来自《当世界年纪还小的时候》这本书的封底，希望我们都能成长为一只大大的南瓜。

