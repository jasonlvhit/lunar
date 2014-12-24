# Some useful functions


def html_escape(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')\
            .replace('"', '&quot;').replace("'", '&#039;')


def sqlite_escape(s):
    return s.replace('\'', '\'\'').replace('/', '//').replace('[', '/[')\
            .replace(']', '/]').replace('%', '/%').replace('&', '/&')\
            .replace('_', '/_').replace('(', '/(').replace(')', '/)')