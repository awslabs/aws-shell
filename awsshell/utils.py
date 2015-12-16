"""Utility module for misc aws shell functions."""
from __future__ import print_function
import os
import awscli
import contextlib
import tempfile
import uuid
import shutil

from awsshell.compat import HTMLParser

AWSCLI_VERSION = awscli.__version__


class FileReadError(Exception):
    pass


def remove_html(html):
    s = DataOnly()
    s.feed(html)
    return s.get_data()


def build_config_file_path(file_name):
    return os.path.join(os.path.expanduser('~'), '.aws', 'shell', file_name)


@contextlib.contextmanager
def temporary_file(mode):
    """Cross platform temporary file creation.

    This is an alternative to ``tempfile.NamedTemporaryFile`` that
    also works on windows and avoids the "file being used by
    another process" error.
    """
    tempdir = tempfile.mkdtemp()
    basename = 'tmpfile-%s' % (uuid.uuid4())
    full_filename = os.path.join(tempdir, basename)
    open(full_filename, 'w').close()
    try:
        with open(full_filename, mode) as f:
            yield f
    finally:
        shutil.rmtree(tempdir)


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
        try:
            with open(filename, mode) as f:
                return f.read()
        except (OSError, IOError) as e:
            raise FileReadError(str(e))

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
        try:
            contents = self._file_mapping[filename]
        except KeyError:
            raise FileReadError(filename)
        if binary:
            contents = contents.encode('utf-8')
        return contents

    def file_exists(self, filename):
        return filename in self._file_mapping
