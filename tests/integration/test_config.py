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
import unittest

from awsshell.app import AWSShell
from awsshell.config import Config


class ConfigTest(unittest.TestCase):

    def setUp(self):
        self.load_config()

    def load_config(self):
        config = Config()
        self.config_obj = config.load('awsshellrc', 'test-awsshellrc')
        self.config_section = self.config_obj['aws-shell']

    def test_config_off(self):
        self.config_section['match_fuzzy'] = False
        self.config_section['enable_vi_bindings'] = False
        self.config_section['show_completion_columns'] = False
        self.config_section['show_help'] = False
        self.config_section['theme'] = 'none'
        self.config_obj.write()
        self.load_config()
        assert self.config_section.as_bool('match_fuzzy') == False
        assert self.config_section.as_bool('enable_vi_bindings') == False
        assert self.config_section.as_bool('show_completion_columns') == False
        assert self.config_section.as_bool('show_help') == False
        assert self.config_section['theme'] == 'none'

    def test_config_on(self):
        self.config_section['match_fuzzy'] = True
        self.config_section['enable_vi_bindings'] = True
        self.config_section['show_completion_columns'] = True
        self.config_section['show_help'] = True
        self.config_section['theme'] = 'vim'
        self.config_obj.write()
        self.load_config()
        assert self.config_section.as_bool('match_fuzzy') == True
        assert self.config_section.as_bool('enable_vi_bindings') == True
        assert self.config_section.as_bool('show_completion_columns') == True
        assert self.config_section.as_bool('show_help') == True
        assert self.config_section['theme'] == 'vim'
