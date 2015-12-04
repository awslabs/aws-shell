"""Module for building the autocompletion indices."""
from __future__ import print_function
import os
import sys
import json
from subprocess import Popen, PIPE

from six import BytesIO
from docutils.core import publish_string
from docutils.writers import manpage
import awscli.clidriver
from awscli.argprocess import ParamShorthandDocGen

from awsshell import determine_doc_index_filename
from awsshell.utils import remove_html
from awsshell import compat


SHORTHAND_DOC = ParamShorthandDocGen()


def new_index():
    return {'arguments': [], 'argument_metadata': {},
            'commands': [], 'children': {}}


def index_command(index_dict, help_command):
    arg_table = help_command.arg_table
    for arg in arg_table:
        arg_obj = arg_table[arg]
        metadata = {
            'required': arg_obj.required,
            'type_name': arg_obj.cli_type_name,
            'minidoc': '',
            'example': '',
            # The name used in the API call/botocore,
            # typically CamelCased.
            'api_name': getattr(arg_obj, '_serialized_name', '')
        }
        if arg_obj.documentation:
            metadata['minidoc'] = remove_html(
                arg_obj.documentation.split('\n')[0])
        if SHORTHAND_DOC.supports_shorthand(arg_obj.argument_model):
            example = SHORTHAND_DOC.generate_shorthand_example(
                arg, arg_obj.argument_model)
            metadata['example'] = example

        index_dict['arguments'].append('--%s' % arg)
        index_dict['argument_metadata']['--%s' % arg] = metadata
    for cmd in help_command.command_table:
        index_dict['commands'].append(cmd)
        # Each sub command will trigger a recurse.
        child = new_index()
        index_dict['children'][cmd] = child
        sub_command = help_command.command_table[cmd]
        sub_help_command = sub_command.create_help_command()
        index_command(child, sub_help_command)


def write_index(output_filename=None):
    driver = awscli.clidriver.create_clidriver()
    help_command = driver.create_help_command()
    index = {'aws': new_index()}
    current = index['aws']
    index_command(current, help_command)

    result = json.dumps(index)
    if not os.path.isdir(os.path.dirname(output_filename)):
        os.makedirs(os.path.dirname(output_filename))
    with open(output_filename, 'w') as f:
        f.write(result)


def write_doc_index(output_filename=None, db=None):
    if output_filename is None:
        output_filename = determine_doc_index_filename()
    driver = awscli.clidriver.create_clidriver()
    help_command = driver.create_help_command()
    user_provided_db = True
    if db is None:
        user_provided_db = False
        db = compat.dbm.open(output_filename, 'c')
    try:
        _index_docs(db, help_command)
        db['__complete__'] = 'true'
    finally:
        if not user_provided_db:
            # If the user provided their own db object,
            # they are responsible for closing it.
            # If we created our own db object, we own
            # closing the db.
            db.close()


def _index_docs(db, help_command):
    for command_name in help_command.command_table:
        command = help_command.command_table[command_name]
        sub_help_command = command.create_help_command()
        text_docs = _render_docs_for_cmd(sub_help_command)
        dotted_name = '.'.join(['aws'] + command.lineage_names)
        db[dotted_name] = text_docs
        _index_docs(db, sub_help_command)


def _render_docs_for_cmd(help_command):
    renderer = FileRenderer()
    help_command.renderer = renderer
    help_command(None, None)
    # The report_level override is so that we don't print anything
    # to stdout/stderr on rendering issues.
    man_contents = publish_string(renderer.contents, writer=manpage.Writer(),
                                  settings_overrides={'report_level': 5})
    cmdline = ['groff', '-man', '-T', 'ascii']
    p = Popen(cmdline, stdin=PIPE, stdout=PIPE, stderr=PIPE)
    groff_output = p.communicate(input=man_contents)[0]
    p2 = Popen(['col', '-bx'], stdin=PIPE, stdout=PIPE, stderr=PIPE)
    text_content = p2.communicate(input=groff_output)[0].decode('utf-8')
    index = text_content.find('DESCRIPTION')
    if index > 0:
        text_content = text_content[index + len('DESCRIPTION'):]
    return text_content


class FileRenderer(object):

    def __init__(self):
        self._io = BytesIO()

    def render(self, contents):
        self._io.write(contents)

    @property
    def contents(self):
        return self._io.getvalue()
