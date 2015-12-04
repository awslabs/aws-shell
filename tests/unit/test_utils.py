from tests import unittest
import os
import tempfile
import shutil

from awsshell.utils import FSLayer
from awsshell.utils import InMemoryFSLayer
from awsshell.utils import FileReadError


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
            self.fslayer.file_contents(self.temporary_filename, binary=True),
            b'helloworld')

    def test_file_exists(self):
        self.assertFalse(self.fslayer.file_exists(self.temporary_filename))

        with open(self.temporary_filename, 'w') as f:
            pass

        self.assertTrue(self.fslayer.file_exists(self.temporary_filename))

    def test_file_does_not_exist_error(self):
        with self.assertRaises(FileReadError):
            self.fslayer.file_contents('/tmp/thisdoesnot-exist.asdf')



class TestInMemoryFSLayer(unittest.TestCase):
    def setUp(self):
        self.file_mapping = {}
        self.fslayer = InMemoryFSLayer(self.file_mapping)

    def test_file_exists(self):
        self.file_mapping['/my/fake/path'] = 'file contents'
        self.assertTrue(self.fslayer.file_exists('/my/fake/path'))

    def test_can_read_file_contents(self):
        self.file_mapping['/myfile'] = 'helloworld'
        self.assertEqual(self.fslayer.file_contents('/myfile'), 'helloworld')
        self.assertEqual(self.fslayer.file_contents('/myfile', binary=True),
                         b'helloworld')

    def test_file_does_not_exist_error(self):
        with self.assertRaises(FileReadError):
            self.fslayer.file_contents('/tmp/thisdoesnot-exist.asdf')
