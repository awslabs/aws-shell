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
import os
import unittest

from awsshell.app import AWSShell
from awsshell.config import Config
from awsshell.utils import build_config_file_path


class ConfigTest(unittest.TestCase):

    def test_config_off(self):
        try:
            os.remove(build_config_file_path('test-awsshellrc'))
        except OSError:
            pass
        self.aws_shell = AWSShell(None, mock.Mock(), mock.Mock())
        self.aws_shell.model_completer.match_fuzzy = False
        self.aws_shell.enable_vi_bindings = False
        self.aws_shell.show_completion_columns = False
        self.aws_shell.show_help = False
        self.aws_shell.theme = 'none'
        self.aws_shell.save_config()
        self.aws_shell.load_config()
        assert self.aws_shell.model_completer.match_fuzzy == False
        assert self.aws_shell.enable_vi_bindings == False
        assert self.aws_shell.show_completion_columns == False
        assert self.aws_shell.show_help == False
        assert self.aws_shell.theme == 'none'

    def test_config_on(self):
        self.aws_shell = AWSShell(None, mock.Mock(), mock.Mock())
        self.aws_shell.model_completer.match_fuzzy = True
        self.aws_shell.enable_vi_bindings = True
        self.aws_shell.show_completion_columns = True
        self.aws_shell.show_help = True
        self.aws_shell.theme = 'vim'
        self.aws_shell.save_config()
        self.aws_shell.load_config()
        assert self.aws_shell.config_section.as_bool('match_fuzzy') == True
        assert self.aws_shell.config_section.as_bool(
            'enable_vi_bindings') == True
        assert self.aws_shell.config_section.as_bool(
            'show_completion_columns') == True
        assert self.aws_shell.config_section.as_bool('show_help') == True
        assert self.aws_shell.config_section['theme'] == 'vim'
