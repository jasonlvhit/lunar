import sys
import re

from ._compat import parse_qs


rule_pattern = re.compile(
    r'''(?P<static>[^<]*) #static
        <(?:
            (?P<type>[a-zA-Z_][a-zA-Z0-9_]*)
            \:
        )?
            (?P<variable>[a-zA-Z_][a-zA-Z0-9_]*)   # variable
        >
    ''', re.VERBOSE
)

valid_methods = [
    'GET',
    'POST',
    'DELETE'
    'PUT',
    'HEAD'
]

def parse_rule(rule):
    pos = 0
    end = len(rule)
    while pos < end:
        m = rule_pattern.match(rule, pos)
        if m is None: # pure static url
            break
        d = m.groupdict()
        _type = d['type']
        _variable = d['variable']
        if d['static'] and len(d['static']) > 0:
            yield None, None, d['static']
        yield _type, _variable, None
        pos = m.end()
    if pos < end:
        r = rule[pos:]
        yield None, None, r

class RouterException(Exception):
    pass


class Rule(object):
    """Route rule object
    """

    def __init__(self, rule, methods):
        self.rule = rule
        if methods is None:
            self.methods = None
        else:
            self.methods = set([x.upper() for x in methods])
            if 'HEAD' not in self.methods and 'GET' in self.methods:
                self.methods.add('HEAD')
            for m in self.methods:
                if m not in valid_methods:
                    raise RouterException("Invalid method %s" % m)

        self._regex = None
        self._trace = []  # for building url
        self.variables = set()
        self.build_regex()


    def build_url(self, values=None):
        if values and len(self.variables) > len(values):
            raise RouterException("Need %d argument to build the URL. Got %d" % (len(self.variables), len(values)))
        url_parts = []
        for _is_dynamic, var in self._trace:
            if _is_dynamic:
                try:
                    url_parts.append(str(values[var]))
                except KeyError:
                    raise RouterException("Need argument '%s' to build the URL." % var)
            else:
                url_parts.append(var)

        return str(u''.join(url_parts))

    def build_regex(self):
        regex_parts = []
        for _type, _variable, _static in parse_rule(self.rule):
            if _type is None and _static:
                regex_parts.append(re.escape(_static))
                self._trace.append((False, _static))
            elif _variable:
                regex_parts.append('(?P<%s>%s)' % (_variable, '[a-zA-Z0-9_]*'))
                self._trace.append((True, _variable))
                self.variables.add(_variable)
        regex = r'^%s$' % (u''.join(regex_parts))
        self._regex = re.compile(regex, re.UNICODE)


class Router(object):

    """Router object for request routing.
    """

    def __init__(self):
        self.rulesMap = {}

    def register(self, path, fn, methods):
        if not callable(fn):
            raise RouterException("Router only accept callable object.")

        r = Rule(path, methods)
        self.rulesMap[r] = fn

    def __call__(self, p, method='GET'):
        return self.get(p, method)

    def get(self, path, method='GET'):
        f, args = self._match_path(path, method=method)
        if not f:
            return None

        return f, args

    def _match_path(self, p, method='GET'):
        for rule, fn in self.rulesMap.items():
            r = rule._regex
            m = r.match(p)

            if m is None:
                continue

            if not method.upper() in rule.methods:
                raise RouterException(
                    "Request method %s not allowed in this app." % method)
            args = {}
            for a in rule.variables:
                args[a] = m.group(a)
            if len(args) == 0:
                args = None
            return fn, args
        return None, None

    def url_for(self, fn, **kwargs):
        if not callable(fn):
            raise RouterException(
                "router url_for method only accept callable object.")
        for rule, v in self.rulesMap.items():
            if v == fn:
                if len(rule.variables) > 0:
                    return rule.build_url(kwargs)
                return rule.build_url()

        raise RouterException(
            "callable object doesn't matched any routing rule.")

    def all_callables(self):
        return self.rulesMap.values()

    def remove_all_routes(self):
        self.rulesMap.clear()
