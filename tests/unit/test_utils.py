from tests import unittest
import os
import tempfile
import datetime
import shutil
import six
import pytest

from awsshell.utils import FSLayer
from awsshell.utils import InMemoryFSLayer
from awsshell.utils import FileReadError
from awsshell.utils import temporary_file
from awsshell.utils import force_unicode
from awsshell.utils import format_json


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


class TestTemporaryFile(unittest.TestCase):
    def test_can_use_as_context_manager(self):
        with temporary_file('w') as f:
            filename = f.name
            f.write("foobar")
            f.flush()
            self.assertEqual(open(filename).read(), "foobar")

    def test_is_removed_after_exiting_context(self):
        with temporary_file('w') as f:
            filename = f.name
            f.write("foobar")
            f.flush()
        self.assertFalse(os.path.isfile(filename))

    def test_can_open_in_read(self):
        with temporary_file('r') as f:
            filename = f.name
            assert f.read() == ''
            # Verify we can open the file again
            # in another file descriptor.
            with open(filename, 'w') as f2:
                f2.write("foobar")
            f.seek(0)
            assert f.read() == "foobar"
        self.assertFalse(os.path.isfile(filename))


strings = ['', u'', 'some text', u'some text', 'yu\u3086', u'yu\u3086']


@pytest.mark.parametrize('text', strings)
def test_force_unicode(text):
    unicode_text = force_unicode(text)
    assert unicode_text == text
    assert isinstance(unicode_text, six.text_type)


def test_force_unicode_binary():
    # should fail decoding and remain unchanged
    blob = '\x81'
    result = force_unicode(blob)
    assert result is blob


def test_force_unicode_recursion():
    obj = {
        'a': ['string'],
        'b': {'str': 'yu\u3086'},
        'c': '\x81',
    }

    clean_obj = force_unicode(obj)
    assert isinstance(clean_obj['a'][0], six.text_type)
    assert isinstance(clean_obj['b']['str'], six.text_type)
    assert clean_obj['c'] is obj['c']
    assert obj == clean_obj


def test_format_json():
    data = {'Key': datetime.datetime(2016, 12, 12)}
    assert format_json(data) == '{\n    "Key": "2016-12-12T00:00:00"\n}'
