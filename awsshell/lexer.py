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
from pygments.lexer import RegexLexer
from pygments.lexer import words
from pygments.token import Keyword, Literal, Name, Operator, Text

from awsshell.index.completion import CompletionIndex


class ShellLexer(RegexLexer):
    """Provides highlighting for commands, subcommands, arguments, and options.

    :type completion_index: :class:`CompletionIndex`
    :param completion_index: Completion index used to determine commands,
        subcommands, arguments, and options for highlighting.

    :type tokens: dict
    :param tokens: A dict of (`pygments.lexer`, `pygments.token`) used for
        pygments highlighting.
    """
    completion_index = CompletionIndex()
    completion_index.load_completions()
    tokens = {
        'root': [
            # ec2, s3, elb...
            (words(
                tuple(completion_index.commands),
                prefix=r'\b',
                suffix=r'\b'),
             Literal.String),
            # describe-instances
            (words(
                tuple(completion_index.subcommands),
                prefix=r'\b',
                suffix=r'\b'),
             Name.Class),
            # --instance-ids
            (words(
                tuple(list(completion_index.args_opts)),
                prefix=r'',
                suffix=r'\b'),
             Keyword.Declaration),
            # --profile
            (words(
                tuple(completion_index.global_opts),
                prefix=r'',
                suffix=r'\b'),
             Operator.Word),
            # Everything else
            (r'.*\n', Text),
        ]
    }
