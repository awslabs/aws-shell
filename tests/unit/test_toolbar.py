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
import unittest
from pygments.token import Token

from awsshell.app import AWSShell
from awsshell.toolbar import Toolbar


class ToolbarTest(unittest.TestCase):

    def setUp(self):
        self.aws_shell = AWSShell(mock.Mock(), mock.Mock(), mock.Mock())
        self.cli = mock.Mock()
        self.toolbar = Toolbar(
            lambda: self.aws_shell.model_completer.match_fuzzy,
            lambda: self.aws_shell.enable_vi_bindings,
            lambda: self.aws_shell.show_completion_columns,
            lambda: self.aws_shell.show_help)

    def test_toolbar_on(self):
        self.aws_shell.model_completer.match_fuzzy = True
        self.aws_shell.enable_vi_bindings = True
        self.aws_shell.show_completion_columns = True
        self.aws_shell.show_help = True
        expected = [
            (Token.Toolbar.On, ' [F2] Fuzzy: ON '),
            (Token.Toolbar.On, ' [F3] Keys: Vi '),
            (Token.Toolbar.On, ' [F4] Multi Column '),
            (Token.Toolbar.On, ' [F5] Help: ON '),
            (Token.Toolbar, ' [F9] Focus: doc '),
            (Token.Toolbar, ' [F10] Exit ')]
        assert expected == self.toolbar.handler(self.cli)

    def test_toolbar_off(self):
        self.aws_shell.model_completer.match_fuzzy = False
        self.aws_shell.enable_vi_bindings = False
        self.aws_shell.show_completion_columns = False
        self.aws_shell.show_help = False
        self.cli.current_buffer_name = 'DEFAULT_BUFFER'
        expected = [
            (Token.Toolbar.Off, ' [F2] Fuzzy: OFF '),
            (Token.Toolbar.On, ' [F3] Keys: Emacs '),
            (Token.Toolbar.On, ' [F4] Single Column '),
            (Token.Toolbar.Off, ' [F5] Help: OFF '),
            (Token.Toolbar, ' [F9] Focus: cli '),
            (Token.Toolbar, ' [F10] Exit ')]
        assert expected == self.toolbar.handler(self.cli)
