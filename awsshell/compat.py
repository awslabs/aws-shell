import sys

PY3 = sys.version_info[0] == 3

if PY3:
    from html.parser import HTMLParser
else:
    from HTMLParser import HTMLParser
