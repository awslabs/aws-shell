"""Module for completion index.

Generates, loads, and writes out completion index.
Also provides an interface for working with the
indexed data.

"""

class FSLayer(object):
    """Abstraction over common OS commands.

    Provides a simpler interface given the operations needed
    by the AWS Shell.

    """

    def file_contents(self, filename, mode='r'):
        """Returns the file for a given filename.

        If you want binary content use ``mode='rb'``.

        """
        with open(filename, mode) as f:
            return f.read()

class CompletionIndex(object):
    pass
