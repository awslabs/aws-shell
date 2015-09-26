import sys

PY3 = sys.version_info[0] == 3

if PY3:
    from html.parser import HTMLParser
    text_type = str
else:
    from HTMLParser import HTMLParser
    text_type = unicode
