#####
Pumpkin. A simple WSGI based webframework for learning.
#####

Pumpkin是一个玩具式的网络框架，基于PEP333和它的进化版PEP3333，它包括一个Router，
一个Template engine，一个简单的WSGI Request和Response的封装，没有任何第三方包的依赖。
项目会不断的演化，在你看到这句话的时候，这个项目还是千疮百孔，下一步会修复很多bug，
重构一些代码，可能会加入基于epoll或者select的异步请求支持。

查看example来看看这是怎么运作的。

Pumpkin is a WSGI based webframework in pure Python, without any third-party dependency. 
Pumpkin include a simple router, which provide the request routing, a template engine 
for template rendering, a simple wrapper for WSGI request and response.

Happy hacking.

::

	from pumpkin.pumpkin import Pumpkin

	@app.route('/', methods = ["GET", "POST"])
	def hello():
		return "Hello, Pumpkin!"

	if __name__ == '__main__':
		app.run()



About pumpkin：

洋葱、萝卜和番茄不相信世界上有南瓜这个东西，它们认为那只是空想。南瓜默默不说话，它只是继续成长。
这句话来自当世界年纪还小的时候这本书的封底，希望我们都能成长为一只大大的南瓜。