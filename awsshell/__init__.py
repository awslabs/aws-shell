from __future__ import unicode_literals, print_function

import os
import sys
import json

from prompt_toolkit.history import InMemoryHistory

from awsshell import shellcomplete
from awsshell import autocomplete
from awsshell import app
from awsshell import docs
from awsshell.compat import StringIO
from awsshell import loaders
from awsshell.index import completion
from awsshell import utils


__version__ = '0.0.1'


def determine_doc_index_filename():
    import awscli
    base = loaders.JSONIndexLoader.index_filename(
        awscli.__version__)
    return base + '.docs'


def load_index(filename):
    load = loaders.JSONIndexLoader()
    return load.load_index(filename)


def main():
    indexer = completion.CompletionIndex()
    try:
        index_str = indexer.load_index(utils.AWSCLI_VERSION)
        index_data = json.loads(index_str)
    except completion.IndexLoadError:
        print("First run, creating autocomplete index...")
        from awsshell.makeindex import write_index
        # TODO: Using internal method, but this will eventually
        # be moved into the CompletionIndex class anyways.
        index_file = indexer._filename_for_version(utils.AWSCLI_VERSION)
        write_index(index_file)
        index_str = indexer.load_index(utils.AWSCLI_VERSION)
        index_data = json.loads(index_str)
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
    doc_data = docs.load_doc_index(doc_index_file)
    completer = shellcomplete.AWSShellCompleter(
        autocomplete.AWSCLIModelCompleter(index_data))
    history = InMemoryHistory()
    shell = app.create_aws_shell(completer, history, doc_data)
    shell.run()


if __name__ == '__main__':
    main()
