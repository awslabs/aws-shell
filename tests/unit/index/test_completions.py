import unittest
import shutil
import tempfile
import os

from awsshell.index import completion
from awsshell.index.completion import FSLayer


class TestCompletionIndex(unittest.TestCase):
    def test_can_load_index(self):
        pass


class TestFSLayer(unittest.TestCase):
    # TestFSLayer provides abstractions over the OS.
    # It is one of the only exceptions in the AWS Shell
    # code where it's ok to test by using actual files.
    # All other test code should use FSLayer.
    def setUp(self):
        self.tempdir = tempfile.mkdtemp()
        self.temporary_filename = os.path.join(
            self.tempdir, 'tempfilefoo')
        self.fslayer = FSLayer()

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def test_can_read_file_contents(self):
        with open(self.temporary_filename, 'w') as f:
            f.write('helloworld')

        self.assertEqual(
            self.fslayer.file_contents(self.temporary_filename),
            'helloworld')
        self.assertEqual(
            self.fslayer.file_contents(self.temporary_filename, mode='rb'),
            b'helloworld')
