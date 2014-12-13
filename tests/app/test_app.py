import os
import sys
import subprocess
import signal
import unittest

try:
	from urllib2 import urlopen
	from urllib2 import HTTPError
except ImportError: 
	from urllib.request import urlopen
	from urllib.error import HTTPError

from . import demo_app

host='localhost'
port=8000

class AppTest(unittest.TestCase):
	def setUp(self):
		args = [sys.executable, demo_app.__file__]
		self.fout = open('/dev/null', 'w')
		self.process = subprocess.Popen(args, stdout=self.fout, stderr=self.fout)

	def tearDown(self):
		self.fout.close()
		self.process.terminate()

	def test_index(self):
		r = urlopen('http://%s:%d/' % (host, port))
		self.assertEqual(r.getcode(), 200)
		self.assertEqual(b'Hello, Pumpkin!', r.read())

	def test_url_for_static(self):
		r = urlopen('http://%s:%d/url_for_static' % (host, port))
		self.assertEqual(r.getcode(), 200)
		url = 'http://%s:%d/static/style.css' % (host, port)
		self.assertIn(url, str(r.read()))

	def test_args(self):
		r = urlopen('http://%s:%d/test_args?key=my_key&count=5' % (host, port))
		self.assertEqual(r.getcode(), 200)
		self.assertEqual(b"('my_key', '5')", r.read())

	def test_redirect(self):
		r = urlopen('http://%s:%d/test_redirect' % (host, port)).read()
		self.assertEqual(b'Hello, Pumpkin!', r)

	def test_404(self):
		self.assertRaises(HTTPError, urlopen, 'http://%s:%d/hello' % (host, port))

	def test_staic(self):
		r = urlopen('http://%s:%d/static/style.css' % (host, port))
		self.assertEqual(r.getcode(), 200)	
