"""Module for completion index.

Generates, loads, and writes out completion index.
Also provides an interface for working with the
indexed data.

The the subpackage docstring of awsshell.index for
a higher level overview.

"""
import os

from awsshell.utils import FSLayer, FileReadError


class IndexLoadError(Exception):
    """Raised when an index could not be loaded."""


class CompletionIndex(object):
    """Handles working with the local commmand completion index."""

    # The completion index can read/write to a cache dir
    # so that it doesn't have to recompute the completion cache
    # every time the CLI starts up.
    DEFAULT_CACHE_DIR = os.path.join(
        os.path.expanduser('~'), '.aws', 'shell', 'cache')

    def __init__(self, cache_dir=DEFAULT_CACHE_DIR, fslayer=None):
        self._cache_dir = cache_dir
        if fslayer is None:
            fslayer = FSLayer()
        self._fslayer = fslayer

    def load_index(self, version_string):
        """Load the completion index for a given CLI version.

        :type version_string: str
        :param version_string: The AWS CLI version, e.g "1.9.2".

        """
        filename = self._filename_for_version(version_string)
        try:
            contents = self._fslayer.file_contents(filename)
        except FileReadError as e:
            raise IndexLoadError(str(e))
        return contents

    def _filename_for_version(self, version_string):
        return os.path.join(
            self._cache_dir, 'completions-%s.json' % version_string)
