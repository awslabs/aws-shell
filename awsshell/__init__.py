from __future__ import unicode_literals

import os
import ast
import sys
import subprocess

from prompt_toolkit.shortcuts import get_input
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.completion import Completer, Completion

from awsshell import autocomplete


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


class AWSCLIAutoCompleter(Completer):
    def __init__(self, completer):
        self._completer = completer

    def get_completions(self, document, complete_event):
        text_before_cursor = document.text_before_cursor
        word_before_cursor = ''
        if text_before_cursor.strip():
            word_before_cursor = text_before_cursor.split()[-1]
        completions = self._completer.autocomplete(text_before_cursor)
        for completion in completions:
            yield Completion(completion, -len(word_before_cursor),
                             display_meta='')


def main():
    index_file = determine_index_filename()
    if not os.path.isfile(index_file):
        raise RuntimeError("Index file not created.  Please run "
                           "aws-shell-mkindex")
    index_data = load_index(index_file)
    completer = AWSCLIAutoCompleter(autocomplete.AWSCLICompleter(index_data))
    history = InMemoryHistory()
    while True:
        try:
            text = get_input('aws> ', completer=completer,
                             history=history)
        except (KeyboardInterrupt, EOFError):
            break
        else:
            full_cmd = 'aws ' + text
            p = subprocess.Popen(full_cmd, shell=True, stdout=subprocess.PIPE)
            for line in p.stdout:
                sys.stdout.write(line)
            p.communicate()


if __name__ == '__main__':
    main()
