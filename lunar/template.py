# -*- coding: utf-8 -*-
"""
A template engine.
"""
import sys
import re
import os
from functools import wraps

if sys.version < '3':
    string_escape = 'string-escape'
else:
    string_escape = 'unicode_escape'


class Walker(object):

    """ Read the source code, provide the token for
        Parser.
    """

    def __init__(self, text):
        self.text = text
        self.cur = 0
        # re token
        self.token = re.compile(r'''
            {{\s+(?P<var>.+?)\s+}} # variable
            | # or
            {%\s+(?P<endblock>end(if|for|try|while|block))\s+%} # endblock
            | # or
            {%\s+(?P<statement>(?P<keyword>\w+)\s*(.*?))\s+%} # statement
            ''', re.VERBOSE)

        self.buffer = []

    @property
    def next_token(self):
        p = self.token.search(self.remain)
        if not p:
            return None
        s = p.start()
        self.buffer.append(self.remain[:s].encode(string_escape))
        self.cur += (s + len(p.group()))
        return p

    @property
    def buffer_before_token(self):
        r = ''.join(i for i in map(lambda x: x.decode('utf-8'), self.buffer))
        self.buffer = []
        return r

    @property
    def empty(self):
        return self.cur >= len(self.text)

    @property
    def remain(self):
        return self.text[self.cur:]

    @property
    def extends(self):
        """The {% extends %} tag is the key here.
        It tells the template engine that this template "extends" another template.
        When the template system evaluates this template, first it locates the parent.

        The extends tag should be the first tag in the template.
        """
        p = re.compile(r'^{%\s+(extends\s*(?P<parent>.*))\s+%}')
        e = p.match(self.text)
        if not e:
            return None
        self.cur += len(e.group())
        return e.group('parent')


class Writer(object):

    """ Writer is a important part of template engine, which provide
        methods for different tokens and blocks. Writer construct a
        intermediate code for Python runtime compiling and executing,
        the main class below 'Template ' will use this code for rendering
        and code generating.
    """

    def __init__(self):
        self.co = []  # python intermediate code
        self._blocks = {}

    def dispatcher(fn):
        @wraps(fn)
        def wrapper(self, s, indent, block):
            p = fn(self, s, indent, block)
            if block:
                self._blocks.get(block).append(p)
            else:
                self.co.append(p)
        return wrapper

    @dispatcher
    def write(self, s, indent, block=None):
        return ''.join([' ' * indent, '_stdout.append(\'\'\'', s, '\'\'\')\n'])

    @dispatcher
    def write_var(self, s, indent, block=None):
        return ''.join([' ' * indent, '_stdout.append(str(', s, '))\n'])

    @dispatcher
    def write_key(self, s, indent, block=None):
        return ''.join([' ' * indent, s, '\n'])

    def write_child(self, c):
        self.co.append(''.join(['block%', c, '\n']))

    def open_block(self, v):
        self._blocks.setdefault(v, [])

    def write_snippet(self, snippet, indent, block=None):
        p = re.compile(r'\n')
        self.co.append(
            p.sub(''.join(['\n', ' ' * indent]), self.shave(''.join(snippet))))

    def shave(self, s):
        p = re.compile(r'(\s+\n)+')
        return p.sub('\n', s)


class TemplateException(Exception):
    pass


class Template(object):

    def __init__(self, source, autoescape=True, path=None):
        self.co = None
        self.walker = Walker(source)
        self.writer = Writer()
        self.parents = None
        self.path = path
        self.autoescape = autoescape
        if source:
            self.co = self.parse().compile()

    def render(self, *args, **context):
        if self.autoescape:
            for (k, v) in context.items():
                if isinstance(v, str):
                    context[k] = self.html_escape(v)

        context['_stdout'] = []
        exec(self.co, context)
        return self.shave_newline(''.join(context['_stdout']))

    def compile(self):
        if self.parents:
            self.writer.co = self.parents.writer.co
        pattern = re.compile(r'block%(?P<name>\w+)')
        _t = ''.join(self.writer.co)
        for g in pattern.finditer(_t):
            if g.group('name') in self.writer._blocks.keys():
                _t = _t.replace(
                    g.group(), ''.join(self.writer._blocks[g.group('name')]))
        return compile(_t, '<string>', 'exec')

    def parse(self):
        indent = 0
        operator = ['if', 'try', 'while', 'for']
        intermediate = ['else', 'elif', 'except', 'finally']
        in_block = []

        def in_block_top():
            if len(in_block):
                return in_block[len(in_block) - 1]
            return None
        _tmp = self.walker.extends
        if _tmp:
            self.parents = Loader(self.path).load(self.shave_dot(_tmp))
        while not self.walker.empty:
            token = self.walker.next_token
            # Just normal text, simply write it out.
            if not token:
                self.writer.write(self.walker.remain, indent, in_block_top())
                break
            self.writer.write(
                self.walker.buffer_before_token, indent, in_block_top())

            variable, endblock, end, statement, keyword, suffix = token.groups(
            )
            if suffix:
                suffix = self.shave_dot(suffix)
            if variable:
                self.writer.write_var(variable, indent, in_block_top())
            elif endblock:
                if end is 'block' and self.parents:
                    in_block.pop()
                indent -= 1
            elif keyword:
                if keyword == "include":
                    c = Loader(self.path).load(suffix).r_co
                    self.writer.write_snippet(c, indent, in_block_top())
                    continue
                elif keyword == "block":
                    if not self.parents:
                        self.writer.write_child(suffix)
                        continue
                    self.writer.open_block(suffix)
                    in_block.append(suffix)
                    continue
                elif keyword not in (intermediate + operator):
                    self.writer.write_key(
                        ' '.join([keyword, suffix]), indent, in_block_top())
                    continue
                if keyword in intermediate:
                    indent -= 1
                self.writer.write_key(
                    ' '.join([keyword, suffix, ':']), indent, in_block_top())
                indent += 1
            else:
                raise TemplateException('Template syntax error.')
        return self

    def html_escape(self, s):
        return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')\
                .replace('"', '&quot;').replace("'", '&#039;')

    @property
    def r_co(self):
        return self.writer.co

    def shave_dot(self, s):
        return re.sub(r'\'|\"', '', s)

    def shave_slash(self, s):
        return re.sub(r'\\n', '\n', s)

    def shave_newline(self, s):
        return re.sub(r'(\s+\n)+', '\n', s)


class Loader(object):

    def __init__(self, root='', e=Template):
        self.root = root
        self.engine = e

    def update_template_engine(self, e):
        self.engine = e

    def load(self, filename):
        if not self.root.endswith(os.sep):
            self.root += os.sep
        p = ''.join([self.root, filename])
        if not os.path.isfile(p):
            raise TemplateException("Template file '%s' does not exist." % p)
        with open(p) as f:
            return self.engine(f.read(), path=self.root)

# template safe escape


def unescape(s):
    """ unescape html tokens.
        <p>{{ unescape(content) }}</p>
    """
    return s.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')\
        .replace('&quot;', '"').replace('&#039;', "'")
