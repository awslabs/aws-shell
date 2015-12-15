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
import sys

from prompt_toolkit.key_binding.input_processor import KeyPress
from prompt_toolkit.keys import Keys
from prompt_toolkit.interface import CommandLineInterface

from tests.compat import unittest
from awsshell.app import AWSShell, InputInterrupt


class KeysTest(unittest.TestCase):

    def setUp(self):
        self.aws_shell = AWSShell(None, mock.Mock(),
                                  None, mock.Mock())
        self.processor = self.aws_shell.cli.input_processor

    def test_F2(self):
        match_fuzzy = self.aws_shell.model_completer.match_fuzzy
        self.processor.feed_key(KeyPress(Keys.F2, ''))
        assert match_fuzzy != self.aws_shell.model_completer.match_fuzzy

    def test_F3(self):
        enable_vi_bindings = self.aws_shell.enable_vi_bindings
        with self.assertRaises(InputInterrupt):
            self.processor.feed_key(KeyPress(Keys.F3, ''))
            assert enable_vi_bindings != self.aws_shell.enable_vi_bindings

    def test_F4(self):
        show_completion_columns = self.aws_shell.show_completion_columns
        with self.assertRaises(InputInterrupt):
            self.processor.feed_key(KeyPress(Keys.F4, ''))
            assert show_completion_columns != \
                self.aws_shell.show_completion_columns

    def test_F5(self):
        show_help = self.aws_shell.show_help
        with self.assertRaises(InputInterrupt):
            self.processor.feed_key(KeyPress(Keys.F5, ''))
            assert show_help != self.aws_shell.show_help

    def test_F10(self):
        # Exiting from the test in this mock test environment will throw:
        #   IOError: [Errno 25] Inappropriate ioctl for device
        # In a non-mock test environment it would through a EOFError.
        # TODO: Probably better to mock the call to event.cli.set_exit().
        with self.assertRaises(IOError) as e:
            self.processor.feed_key(KeyPress(Keys.F10, ''))
