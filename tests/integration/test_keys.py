# Copyright 2015 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
#     http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.
import mock

from prompt_toolkit.input import PipeInput
from prompt_toolkit.output import DummyOutput
from prompt_toolkit.key_binding.input_processor import KeyPress
from prompt_toolkit.keys import Keys

from tests.compat import unittest
from awsshell.app import AWSShell, InputInterrupt


class KeysTest(unittest.TestCase):

    def setUp(self):
        self.input = PipeInput()
        output = DummyOutput()
        self.aws_shell = AWSShell(None, mock.Mock(), mock.Mock(),
                                  input=self.input, output=output)
        self.processor = self.aws_shell.cli.input_processor

    def tearDown(self):
        self.input.close()

    def feed_key(self, key):
        self.processor.feed(KeyPress(key, u''))
        self.processor.process_keys()

    def test_F2(self):
        match_fuzzy = self.aws_shell.model_completer.match_fuzzy
        self.feed_key(Keys.F2)
        assert match_fuzzy != self.aws_shell.model_completer.match_fuzzy

    def test_F3(self):
        enable_vi_bindings = self.aws_shell.enable_vi_bindings
        with self.assertRaises(InputInterrupt):
            self.feed_key(Keys.F3)
        assert enable_vi_bindings != self.aws_shell.enable_vi_bindings

    def test_F4(self):
        show_completion_columns = self.aws_shell.show_completion_columns
        with self.assertRaises(InputInterrupt):
            self.feed_key(Keys.F4)
        assert show_completion_columns != \
            self.aws_shell.show_completion_columns

    def test_F5(self):
        show_help = self.aws_shell.show_help
        with self.assertRaises(InputInterrupt):
            self.feed_key(Keys.F5)
        assert show_help != self.aws_shell.show_help

    def test_F9(self):
        assert self.aws_shell.cli.current_buffer_name == u'DEFAULT_BUFFER'
        self.feed_key(Keys.F9)
        assert self.aws_shell.cli.current_buffer_name == u'clidocs'

    def test_F10(self):
        self.feed_key(Keys.F10)
        assert self.aws_shell.cli.is_exiting
