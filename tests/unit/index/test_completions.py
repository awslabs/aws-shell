import unittest

from awsshell.index import completion
from awsshell.utils import InMemoryFSLayer


class TestCompletionIndex(unittest.TestCase):
    def setUp(self):
        # filename -> file content
        self.files = {}
        self.fslayer = InMemoryFSLayer(self.files)

    def test_can_load_index(self):
        c = completion.CompletionIndex(cache_dir='/tmp/cache',
                                       fslayer=self.fslayer)
        self.files['/tmp/cache/completions-1.9.1.json'] = '{}'
        try:
            c.load_index('1.9.1')
        except completion.IndexLoadError as e:
            self.fail("Expected to load index for '1.9.1', "
                      "but was unable.")

    def test_index_does_not_exist_raises_error(self):
        c = completion.CompletionIndex(cache_dir='/tmp/cache',
                                       fslayer=self.fslayer)
        with self.assertRaises(completion.IndexLoadError):
            c.load_index('1.9.1')
