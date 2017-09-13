from tests.compat import unittest
from time import sleep
from hecate.hecate import Runner, Timeout

class UITest(unittest.TestCase):

    def setUp(self):
        self.shell = Runner(u'aws-shell')

    def tearDown(self):
        self.shell.shutdown()

    def test_docs_are_searchable(self):
        shell = self.shell
        shell.await_text(u'aws>', timeout=2)
        shell.write(u'ec2 ')
        shell.await_text(u'Amazon EC2')
        shell.press(u'F9')
        shell.write(u'/')
        # wait for the input timeout to trigger
        sleep(1)
        # ensure documentation panel is still there
        shell.await_text(u'Amazon EC2')
