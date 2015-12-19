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

from awsshell.index.completion import CompletionIndex


class LoadCompletionsTest(unittest.TestCase):

    def setUp(self):
        self.completion_index = CompletionIndex()
        # This would probably be cleaner with a pytest.fixture like
        # test_completions.index_data
        DATA = (
            '{"aws": '
            '{"commands": ["devicefarm", "foo"], '
            '"arguments": ["--debug", "--endpoint-url"], '
            '"children": {"devicefarm": '
            '{"commands": ["create-device-pool"], '
            '"children": {"create-device-pool": '
            '{"commands": [], '
            '"arguments": ["--project-arn", "--name"]}}}, '
            '"foo": '
            '{"commands": ["bar"], '
            '"children": {"bar": '
            '{"commands": [], "arguments": ["--baz"]}}}}}}'
        )
        self.completion_index.load_index = lambda x: DATA
        self.completion_index.load_completions()

    def test_load_completions(self):
        assert self.completion_index.commands == [
            'devicefarm', 'foo']
        assert self.completion_index.subcommands == [
            'create-device-pool', 'bar']
        assert self.completion_index.global_opts == [
            '--debug', '--endpoint-url']
        assert self.completion_index.args_opts == set([
            '--project-arn', '--name', '--baz'])
