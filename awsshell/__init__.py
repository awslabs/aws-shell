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
from awsshell import docs
from awsshell.compat import StringIO
from awsshell import loaders


__version__ = '0.0.1'


def determine_index_filename():
    # Calculate where we should write out the index file.
    # The intent is that an index file is tied to a specific
    # CLI version, so if you update your CLI, then you need to
    # update your version.
    import awscli
    return loaders.JSONIndexLoader.index_filename(
        awscli.__version__)


def determine_doc_index_filename():
    return determine_index_filename() + '.docs'


def load_index(filename):
    load = loaders.JSONIndexLoader()
    return load.load_index(filename)


def main():
    index_file = determine_index_filename()
    if not os.path.isfile(index_file):
        print("First run, creating autocomplete index...")
        from awsshell.makeindex import write_index
        write_index(index_file)
    doc_index_file = determine_doc_index_filename()
    if not os.path.isfile(doc_index_file):
        # TODO: Run in background.  Also capture
        # stdout/stderr. Our doc generation process generates
        # a lot of warnings/noise from the renderers.
        print("First run, creating doc index, this will "
              "take a few minutes, but only needs to run "
              "once.")
        from awsshell.makeindex import write_doc_index
        sys.stderr = StringIO()
        try:
            write_doc_index()
        finally:
            sys.stderr = sys.__stderr__
    index_data = load_index(index_file)
    doc_data = docs.load_doc_index(doc_index_file)
    completer = shellcomplete.AWSShellCompleter(
        autocomplete.AWSCLIModelCompleter(index_data))
    history = InMemoryHistory()
    shell = app.create_aws_shell(completer, history, doc_data)
    shell.run()


if __name__ == '__main__':
    main()
