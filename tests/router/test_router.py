import unittest

from lunar.router import Router, RouterException


def just_a_callable():
    pass


def another_callable():
    pass


class RouterTest(unittest.TestCase):

    def setUp(self):
        self.router = Router()

    def tearDown(self):
        self.router = None

    def test_register_with_not_callable(self):
        self.assertRaises(
            RouterException, self.router.register, '/', '10', ['GET'])

    def test_register_with_callable_and_legal_path(self):
        self.router.register('/', just_a_callable, ['GET'])
        self.assertIn(just_a_callable, self.router.methods['GET'])

    def test_call_magic_method(self):
        self.router.register('/', just_a_callable, ['GET'])
        r = self.router('/')
        self.assertEqual(r, (just_a_callable, None))

    def test_register_with_callable_and_illegal_path(self):
        self.assertRaises(
            RouterException, self.router.register, '$$', just_a_callable, ['GET'])

    def test_get_with_illegal_methods(self):
        self.router.register('/', just_a_callable, ['GET'])
        self.assertRaises(RouterException, self.router.get, '/', 'REMOVE')

    def test_get_with_legal_methods_one_slash(self):
        self.router.register('/', just_a_callable, ['GET'])
        self.assertEqual((just_a_callable, None), self.router.get('/'))

    def test_get_with_legal_methods_two_slash(self):
        self.router.register('/post/about', just_a_callable, ['GET'])
        self.assertEqual(
            (just_a_callable, None), self.router.get('/post/about'))

    def test_get_with_int_args(self):
        self.router.register('/show/<int:id>', just_a_callable, ['GET'])
        self.assertEqual(
            (just_a_callable, {'id': '1'}), self.router.get('/show/1'))

    def test_url_for_with_not_callable(self):
        self.assertRaises(RouterException, self.router.url_for, '10')

    def test_url_for_with_no_args_rule(self):
        self.router.register('/post', just_a_callable, ['GET'])
        self.assertEqual('/post', self.router.url_for(just_a_callable))

    def test_url_for_with_args_rule_but_no_args_provided(self):
        self.router.register('/post/<int:id>', just_a_callable, ['GET'])
        self.assertRaises(
            RouterException, self.router.url_for, just_a_callable)

    def test_url_for_with_args_rule_and_args_provided(self):
        self.router.register('/post/<int:id>', just_a_callable, ['GET'])
        self.assertEqual(
            '/post/1', self.router.url_for(just_a_callable, id='1'))

    def test_url_for_with_no_matched_rule(self):
        self.router.register('/post', just_a_callable, ['GET'])
        self.assertRaises(
            RouterException, self.router.url_for, another_callable)

    def test_all_callable(self):
        self.router.register('/', just_a_callable, ['GET'])
        r = self.router.all_callables()
        self.assertEqual(set(r), set([just_a_callable]))
        self.router.register('/post', another_callable, ['GET'])
        r = self.router.all_callables()
        self.assertEqual(set(r), set([another_callable, just_a_callable]))
