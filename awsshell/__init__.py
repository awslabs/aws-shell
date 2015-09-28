from __future__ import unicode_literals

import os
import ast
import sys
import subprocess
import tempfile

from prompt_toolkit.shortcuts import get_input
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.completion import Completer, Completion

from awsshell import autocomplete
from awsshell import app


NOOP = {'arguments': [], 'commands': [], 'children': {}}


__version__ = '0.0.1'


def determine_index_filename():
    # Calculate where we should write out the index file.
    # The intent is that an index file is tied to a specific
    # CLI version, so if you update your CLI, then you need to
    # update your version.
    import awscli
    return os.path.join(
        os.path.expanduser('~'), '.aws', 'shell',
        '%s-completions.idx' % awscli.__version__,
    )


def load_index(filename):
    with open(filename, 'r') as f:
        return ast.literal_eval(f.read())


class AWSShellCompleter(Completer):
    """Completer class for the aws-shell.

    This is the completer used specifically for the aws shell.
    Not to be confused with the AWSCLICompleter, which is more
    low level, and can be reused in contexts other than the
    aws shell.
    """
    def __init__(self, completer):
        self._completer = completer

    @property
    def completer(self):
        return self._completer

    @completer.setter
    def completer(self, value):
        self._completer = value

    def get_completions(self, document, complete_event):
        text_before_cursor = document.text_before_cursor
        word_before_cursor = ''
        if text_before_cursor.strip():
            word_before_cursor = text_before_cursor.split()[-1]
        completions = self._completer.autocomplete(text_before_cursor)
        arg_meta = self._completer.arg_metadata
        for completion in completions:
            if completion.startswith('--') and completion in arg_meta:
                # TODO: Need to handle merging in global options as well.
                meta = arg_meta[completion]
                if meta['required']:
                    display_text = '%s (required)' % completion
                else:
                    display_text = completion
                type_name = arg_meta[completion]['type_name']
                display_meta = '[%s] %s' % (type_name, arg_meta[completion]['minidoc'])
            else:
                display_text = completion
                display_meta = ''
            if text_before_cursor and text_before_cursor[-1] == ' ':
                location = 0
            else:
                location = -len(word_before_cursor)
            yield Completion(completion, location,
                             display=display_text, display_meta=display_meta)


def main():
    index_file = determine_index_filename()
    if not os.path.isfile(index_file):
        print("First run, creating autocomplete index...")
        from awsshell.makeindex import write_index
        write_index()
    index_data = load_index(index_file)
    completer = AWSShellCompleter(autocomplete.AWSCLICompleter(index_data))
    history = InMemoryHistory()
    shell = app.create_aws_shell(completer, history)
    shell.run()


if __name__ == '__main__':
    main()
