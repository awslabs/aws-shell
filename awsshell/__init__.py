from __future__ import unicode_literals

import os
import ast
import sys
import subprocess
import tempfile

from prompt_toolkit.shortcuts import get_input
from prompt_toolkit.history import InMemoryHistory

from awsshell import shellcomplete
from awsshell import autocomplete
from awsshell import app


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


def main():
    index_file = determine_index_filename()
    if not os.path.isfile(index_file):
        print("First run, creating autocomplete index...")
        from awsshell.makeindex import write_index
        write_index()
    index_data = load_index(index_file)
    completer = shellcomplete.AWSShellCompleter(
        autocomplete.AWSCLICompleter(index_data))
    history = InMemoryHistory()
    shell = app.create_aws_shell(completer, history)
    shell.run()


if __name__ == '__main__':
    main()
