from __future__ import unicode_literals, print_function

import json
import argparse
import threading

from awsshell import shellcomplete
from awsshell import autocomplete
from awsshell import app
from awsshell import docs
from awsshell import loaders
from awsshell.index import completion
from awsshell import utils


__version__ = '0.1.0'


def determine_doc_index_filename():
    import awscli
    base = loaders.JSONIndexLoader.index_filename(
        awscli.__version__)
    return base + '.docs'


def load_index(filename):
    load = loaders.JSONIndexLoader()
    return load.load_index(filename)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--profile', help='The profile name to use '
                        'when starting the AWS Shell.')
    args = parser.parse_args()

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
    from awsshell.makeindex import write_doc_index
    doc_data = docs.load_lazy_doc_index(doc_index_file)
    # There's room for improvement here.  If the docs didn't finish
    # generating, we regen the whole doc index.  Ideally we pick up
    # from where we left off.
    try:
        docs.load_doc_db(doc_index_file)['__complete__']
    except KeyError:
        print("Creating doc index in the background. "
              "It will be a few minutes before all documentation is "
              "available.")
        t = threading.Thread(target=write_doc_index, args=(doc_index_file,))
        t.daemon = True
        t.start()
    model_completer = autocomplete.AWSCLIModelCompleter(index_data)
    completer = shellcomplete.AWSShellCompleter(model_completer)
    shell = app.create_aws_shell(completer, model_completer, doc_data)
    if args.profile:
        shell.profile = args.profile
    shell.run()


if __name__ == '__main__':
    main()
