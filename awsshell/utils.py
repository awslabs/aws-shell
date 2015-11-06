"""Utility module for misc aws shell functions."""
import os

from awsshell.compat import HTMLParser


def remove_html(html):
    s = DataOnly()
    s.feed(html)
    return s.get_data()


class DataOnly(HTMLParser):
    def __init__(self):
        # HTMLParser is an old-style class, which can't be used with super()
        HTMLParser.__init__(self)
        self.reset()
        self.lines = []

    def handle_data(self, data):
        self.lines.append(data)

    def get_data(self):
        return ''.join(self.lines)


class FSLayer(object):
    """Abstraction over common OS commands.

    Provides a simpler interface given the operations needed
    by the AWS Shell.

    """
    def file_contents(self, filename, binary=False):
        """Returns the file for a given filename.

        If you want binary content use ``mode='rb'``.

        """
        if binary:
            mode = 'rb'
        else:
            mode = 'r'
        with open(filename, mode) as f:
            return f.read()

    def file_exists(self, filename):
        """Checks if a file exists.

        This method returns true if:

            * The file exists.
            * The filename is a file (not a directory).

        """
        return os.path.isfile(filename)


class InMemoryFSLayer(object):
    """Same interface as FSLayer with an in memory implementation."""

    def __init__(self, file_mapping):
        # path -> file_contents
        # file_contents are expected to be text, not
        # binary.
        self._file_mapping = file_mapping

    def file_contents(self, filename, binary=False):
        contents = self._file_mapping[filename]
        if binary:
            contents = contents.encode('utf-8')
        return contents

    def file_exists(self, filename):
        return filename in self._file_mapping
