from __future__ import print_function
import sys
import platform


PY3 = sys.version_info[0] == 3
ON_WINDOWS = platform.system() == 'Windows'


if PY3:
    from html.parser import HTMLParser
    text_type = str
    from io import StringIO
    import dbm
else:
    from HTMLParser import HTMLParser
    text_type = unicode
    from cStringIO import StringIO
    import anydbm as dbm


if ON_WINDOWS:
    def default_editor():
        return 'notepad.exe'
else:
    def default_editor():
        return 'vim'
