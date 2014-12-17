"""
Bottle-like Servers strategy.

Method lunar.run accept a subclass of ServerAdapter, create a server 
instance and run applications using the run interface provided by ServerAdapter.

So the server must implement the interface 'run' provided by ServerAdapter.
"""


class ServerAdapter(object):

    def __init__(self, host="127.0.0.1", port=8000):
        self.host = host
        self.port = port

    def __repr__(self):
        return "%s (%s:%s)" % (self.__class__.__name__, self.host, self.port)

    def run(self, app):
        pass


class WSGIRefServer(ServerAdapter):

    def run(self, app):
        from wsgiref.simple_server import make_server
        httpd = make_server(self.host, self.port, app)
        httpd.serve_forever()


class TornadoServer(ServerAdapter):

    """Tornado server for test and example.
    """

    def run(self, app):
        import tornado.wsgi
        import tornado.httpserver
        import tornado.ioloop
        container = tornado.wsgi.WSGIContainer(app)
        server = tornado.httpserver.HTTPServer(container)
        server.listen(port=self.port, address=self.host)
        tornado.ioloop.IOLoop.instance().start()


class TwistedServer(ServerAdapter):

    """Twisted server for test purpose
    """

    def run(self, app):
        from twisted.web import server, wsgi
        from twisted.internet import reactor
        resource = wsgi.WSGIResource(reactor, reactor.getThreadPool(), app)
        server = server.Site(resource)
        reactor.listenTCP(port=self.port, factory=server, interface=self.host)
        reactor.run()


