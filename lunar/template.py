# -*- coding: utf-8 -*-
"""
    lunar.template
    ~~~~~~~~~~~~~~

    template module provide a simple template system that compiles
    templates to Python code which like django and tornado template
    modules.

    Usage
    -----

    Well, you can view the tests file directly for the usage under tests.

    Basically::

            >>> from lunar import template
            >>> template.Template('Hello, {{ name }}').render(name = 'lunar')
            Hello, lunar

    If, else, for...::

            >>> template.Template('''
            ... {% for i in l %}
            ...    {% if i > 3 %}
            ...    	{{ i }}
            ...    {% else %}
            ... 	less than 3
            ...    {% endif %}
            ... {% endfor %})
            ... ''' ).render(l = [2, 4])
            less than 3
            4

    Then, user define class object maybe also works well::

            >>> class A(object):
            ...
            ...    def __init__(self, a, b):
            ...        self.a = a
            ...        self.b = b
            ...
            >>> o = A("I am o.a", [1, 2, 3])
            >>> template.Template('''
            ...    {{ o.a }}
            ...    {% for i in o.b %}
            ...    	{{ i }}
            ...    {% endfor %}
            ... ''').render(o=o)
            I am o.a
            1
            2
            3

    and Wow, function maybe suprise you::

            >>> template.Template('{{ abs(-3) }}').render()
            '3'
            >>> template.Template('{{ len([1, 2, 3]) }}').render()
            '3'
            >>> template.Template('{{ [1, 2, 3].index(2) }}').render()
            '1'

    and complex function like lambda expression maybe works::

            >>> template.Template('{{ list(map(lambda x: x * 2, [1, 2, 3])) }}').render()
            '[2, 4, 6]'

    and lastly, inheritance of template, extends and include::

            {% extends 'layout.html' %}
            {% include 'snippets.html' %}

    Hacking with fun and joy.

"""
import collections
import os
import re
import sys

# REFACTORING TODO: [[[escape]]]
# from .util import html_escape

# TODO: escape options
_DEFAULT_ESCAPE_OPTION = "maybe_escape_option"


# LRU Cache capacity:
_DEFAULT_CACHECAPACITY = 128

# Inner variable of compiled template source code
# which is a Python list, contain all the output
# statement of Python code
_DEFAULT_STDOUT = "_stdout"

if sys.version < '3':
    string_escape = "string-escape"
else:
    string_escape = "unicode_escape"


class Scanner(object):

    """ Scanner is a inner class of Template which provide
    custom template source reading operations.

    """

    def __init__(self, source):
        self.source = source
        self.cur = 0
        # regular expressions for token catching.
        self.re_token = re.compile(r'''
        {{\s+(?P<var>.+?)\s+}} # variable
        | # or
        {%\s+(?P<endblock>end(if|for|try|while|block))\s+%} # endblock
        | # or
        {%\s+(?P<statement>(?P<keyword>\w+)\s*(.*?))\s+%} # statement
        ''', re.VERBOSE)

        # buffer for readed but not used token.
        self.buffer = []

    @property
    def remain(self):
        """ Get remaining text which have not been processed.
        """
        return self.source[self.cur:]

    @property
    def next_token(self):
        """ Get the next token which match the re_token semantic.
        return None if there is no more tokens, otherwise,
        return matched regular expression group of token p, move forward
        and push the remain source text into buffer at the same time.

        """
        p = self.re_token.search(self.remain)
        if not p:
            return None
        # move forward.
        s = p.start()
        self.buffer.append(self.remain[:s].encode(string_escape))
        self.cur += (s + len(p.group()))

        return p

    @property
    def buffer_before_token(self):
        """ Get the buffer text before token, and clear the buffer.

            TODO: maybe a better solution for unicode or bytes processing.

        """
        r = ''.join(i for i in map(lambda x: x.decode('utf-8'), self.buffer))
        self.buffer = []
        return r

    @property
    def empty(self):
        """ Return true if self.cur >= source text length.

        """
        return self.cur >= len(self.source)

    @property
    def extends(self):
        """The {% extends %} tag tells the template engine that
        this template "extends" another template.

        When the template system evaluates this template, first it locates the parent.
        The extends tag should be the first tag in the template.
        """
        p = re.compile(r'^{%\s+(extends\s*(?P<parent>.*))\s+%}')
        e = p.match(self.source)
        # extends detact must be done at the begining of parsing.
        # return None if there is no extends tag.
        if not e:
            return None
        self.cur += len(e.group())
        return e.group('parent')


class BaseNode(object):

    """ Base abstract class for nodes.
    Subclass of BaseNode must implement 'generate' interface for
    output Python intermediate code generating.

    """

    def __init__(self, text, indent, block):
        self.text = text
        self.indent = indent
        self.block = block

    def _write(self, text, wfile):
        if not self.block:
            wfile.intermediate.append(text)
        else:
            wfile.blocks[self.block].append(text)

    def generate(self, wfile):
        raise NotImplementedError()


class KeyNode(BaseNode):

    """ Node for keywords like if else...

    """

    def generate(self, wfile):
        self._write(
            ''.join([' ' * self.indent, self.text, '\n']), wfile)


class TextNode(BaseNode):

    """ Node for normal text

    """

    def generate(self, wfile):

        self._write(''.join(
            [' ' * self.indent, wfile.stdout,
             '.append(\'\'\'', self.text, '\'\'\')\n']), wfile)


class VariableNode(BaseNode):

    """ Node for variables:
        such as {{ name }}

    """

    def generate(self, wfile):
        self._write(''.join([' ' * self.indent, wfile.stdout,
                             '.append(str(', self.text, '))\n']), wfile)


class SnippetNode(BaseNode):

    def generate(self, wfile):
        p = re.compile(r'\n')
        self.text = re.compile(r'(\s+\n)+').sub('\n', ''.join(self.text))
        wfile.intermediate.append(
            p.sub(''.join(['\n', ' ' * self.indent]), self.text))


class ChildNode(BaseNode):

    def __init__(self, name):
        self.name = name

    def generate(self, wfile):
        wfile.intermediate.append(
            ''.join(['block%', self.name, '\n']))


class Writer(object):

    def __init__(self):
        self.stdout = _DEFAULT_STDOUT
        self.blocks = {}
        self.namespace = {}

        # Generated Python intermediate code.
        self.intermediate = []

    def update_namespace(self, name):
        self.blocks.setdefault(name, [])

    def generate(self, nodes=None):
        (node.generate(self) for node in nodes)


class TemplateException(Exception):
    pass


class Template(object):

    """ Main class for compiled template instance.

    A initialized template instance will parse and compile
    all the template source to Python intermediate code,
    and instance function 'render' will use Python builtin function
    'exec' to execute the intermediate code in Python
    runtime.

    As function 'exec' own very strong power and the ability to
    execute all the python code in the runtime with given
    namespace dict, so this template engine can perform all
    the python features even lambda function. But, function
    'exec' also has a huge problem in security, so be careful
    and be serious, and I am very serious too.

    """
    operator = ['if', 'try', 'while', 'for']
    intermediate = ['else', 'elif', 'except', 'finally']

    def __init__(self, source, path=None, escape_option=None):

        self.nodes = []
        self.scanner = Scanner(source)
        self.writer = Writer()

        # parents templates
        self.parents = None

        # path for extends and include
        self.path = path

        # compiled intermediate code.
        self.intermediate = None

        if source:
            self._parse()
            self.writer.generate(self.nodes)
            self.intermediate = self._compile()

    @property
    def intermediate_list(self):
        return self.writer.intermediate

    def _parse(self):
        indent = 0
        in_block = []

        def in_block_top():
            if len(in_block):
                return in_block[len(in_block) - 1]
            return None

        # firstly, detect the extends tag.
        # if _ext, load the parents template
        _ext = self.scanner.extends
        if _ext:
            # trim the quotes
            _ext = re.sub(r'\'|\"', '', _ext)
            if self.path is None:
                raise TemplateException(
                    "Template path must set when extends tag used.")
            self.parents = Loader(self.path).load(_ext)

        while not self.scanner.empty:
            token = self.scanner.next_token
            # Text node , simply write it out.
            if not token:
                self.nodes.append(
                    TextNode(self.scanner.remain, indent, in_block_top()))
                break
            # write the remaining text before token.
            self.nodes.append(
                TextNode(self.scanner.buffer_before_token, indent, in_block_top()))

            variable, endblock, end, statement, keyword, suffix = token.groups(
            )
            # print(variable, endblock, end, statement, keyword, suffix)
            if variable:
                self.nodes.append(
                    VariableNode(variable, indent, in_block_top()))
            elif endblock:
                # enclose a block.
                # pop it from block stack,
                # if stack is None, raise Exception.
                # indent = indent - 1 at the same time.
                if end is 'block' and len(in_block) == 0:
                    raise TemplateException("Invalid endblock tag.")
                if end is 'block' and self.parents:
                    in_block.pop()
                indent -= 1
            elif keyword:
                if keyword == "include":
                    # child template:
                    # get child template intermediate code
                    # update it into namespace
                    suffix = re.sub(r'\'|\"', '', suffix)

                    if self.path is None:
                        raise TemplateException(
                            "Template path must set when include tag used.")
                    c = Loader(self.path).load(suffix).intermediate_list
                    self.nodes.append(SnippetNode(c, indent, in_block_top()))
                    continue
                elif keyword == "block":
                    if not self.parents:
                        self.nodes.append(ChildNode(suffix))
                        continue
                    self.writer.update_namespace(suffix)
                    in_block.append(suffix)
                    continue
                elif keyword not in (self.intermediate + self.operator):
                    self.nodes.append(KeyNode(
                        ' '.join([keyword, suffix]), indent, in_block_top()))
                    continue
                if keyword in self.intermediate:
                    indent -= 1
                self.nodes.append(KeyNode(
                    ' '.join([keyword, suffix, ':']), indent, in_block_top()))
                indent += 1
            else:
                raise TemplateException('Template syntax error.')
        # return self if needed.
        # return self

    def render(self, *args, **context):
        for arg in args:
            context.update(arg)

        # TODO: handler escape.
        # if self.autoescape:
        #    for (k, v) in context.items():
        #       if isinstance(v, str):
        #            context[k] = html_escape(v)

        context['_stdout'] = []
        exec(self.intermediate, context)
        return re.sub(r'(\s+\n)+', '\n', ''.join(context[self.writer.stdout]))

    def _compile(self):
        # Process parent template files firstly.
        if self.parents:
            self.writer.intermediate \
                = self.parents.writer.intermediate

        # Update blocks
        pattern = re.compile(r'block%(?P<name>\w+)')
        _t = ''.join(self.writer.intermediate)
        for g in pattern.finditer(_t):
            if g.group('name') in self.writer.blocks.keys():
                _t = _t.replace(
                    g.group(), ''.join(self.writer.blocks[g.group('name')]))
        return compile(_t, '<string>', 'exec')


class LRUCache(object):

    """ Simple LRU cache for template instance caching.

        in fact, the OrderedDict in collections module or
        @functools.lru_cache is working well too.

    """

    def __init__(self, capacity=_DEFAULT_CACHECAPACITY):
        self.capacity = capacity
        self.cache = collections.OrderedDict()

    def get(self, key):
        """ Return -1 if catched KeyError exception.

        """
        try:
            value = self.cache.pop(key)
            self.cache[key] = value
            return value
        except KeyError:
            return -1

    def set(self, key, value):
        try:
            self.cache.pop(key)
        except KeyError:
            if len(self.cache) >= self.capacity:
                self.cache.popitem(last=False)
        self.cache[key] = value


class Loader(object):

    """ Lunar use a template Loader which loads the environments of
    main Lunar application, or just give the template system a root
    directory to search the template files.

        loader = template.Loader("home/to/root/of/templates/")
        loader.load("index.html").render()

    Loader class use a LRU cache system to cache the recently used
    templates for performance consideration.
    """

    def __init__(self, root='', engine=Template,
                 escape_option=_DEFAULT_ESCAPE_OPTION,
                 cache_capacity=_DEFAULT_CACHECAPACITY):
        self.root = root
        self.engine = engine

        # TODO: escape option
        self.escape_option = escape_option

        self.cache = LRUCache(capacity=cache_capacity)

    def update_engine(self, e, escape_option=_DEFAULT_ESCAPE_OPTION):
        self.engine = e

        # TODO:
        self.escape_option = escape_option

    def load(self, filename):
        if not self.root.endswith(os.sep) and self.root != '':
            self.root += os.sep
        p = ''.join([self.root, filename])

        # Use the cached template instance firstly
        # TODO: add LRU tests.
        cache_instance = self.cache.get(p)
        if cache_instance != -1:
            return cache_instance

        if not os.path.isfile(p):
            raise TemplateException("Template file '%s' does not exist." % p)

        with open(p) as f:
            self.cache.set(p, self.engine(f.read(), path=self.root))
        return self.cache.get(p)


# TODO: remove this function

def unescape(s):
    """ unescape html tokens.
        <p>{{ unescape(content) }}</p>
    """
    return s.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')\
        .replace('&quot;', '"').replace('&#039;', "'")
