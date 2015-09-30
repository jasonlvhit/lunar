"""
Python 2 & 3 compatibility
"""

import sys

if sys.version < '3':
    import httplib
    from urlparse import parse_qs
    from Cookie import SimpleCookie

    string_escape = "string-escape"

else:
    import http.client as httplib
    from http.cookies import SimpleCookie
    from urllib.parse import parse_qs

    string_escape = "unicode_escape"
