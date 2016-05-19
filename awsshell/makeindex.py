"""Module for building the autocompletion indices."""
from __future__ import print_function
import os
import json

from six import BytesIO
from docutils.core import publish_string
from botocore.docs.bcdoc import textwriter
import awscli.clidriver
from awscli.argprocess import ParamShorthandDocGen

from awsshell import determine_doc_index_filename
from awsshell.utils import remove_html
from awsshell import docs


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
            service_name, op_name = help_command.event_class.rsplit('.', 1)
            example = SHORTHAND_DOC.generate_shorthand_example(
                cli_argument=arg_obj,
                service_name=service_name,
                operation_name=op_name,
            )
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


def write_doc_index(output_filename=None, db=None, help_command=None):
    if output_filename is None:
        output_filename = determine_doc_index_filename()
    user_provided_db = True
    if db is None:
        user_provided_db = False
        db = docs.load_doc_db(output_filename)
    if help_command is None:
        driver = awscli.clidriver.create_clidriver()
        help_command = driver.create_help_command()

    should_close = not user_provided_db
    do_write_doc_index(db, help_command, close_db_on_finish=should_close)


def do_write_doc_index(db, help_command, close_db_on_finish):
    try:
        _index_docs(db, help_command)
        db['__complete__'] = 'true'
    finally:
        if close_db_on_finish:
            # If the user provided their own db object,
            # they are responsible for closing it.
            # If we created our own db object, we own
            # closing the db.
            db.close()


def _index_docs(db, help_command):
    for command_name in help_command.command_table:
        command = help_command.command_table[command_name]
        sub_help_command = command.create_help_command()
        text_docs = render_docs_for_cmd(sub_help_command)
        dotted_name = '.'.join(['aws'] + command.lineage_names)
        db[dotted_name] = text_docs
        _index_docs(db, sub_help_command)


def render_docs_for_cmd(help_command):
    renderer = FileRenderer()
    help_command.renderer = renderer
    help_command(None, None)
    # The report_level override is so that we don't print anything
    # to stdout/stderr on rendering issues.
    original_cli_help = renderer.contents.decode('utf-8')
    text_content = convert_rst_to_basic_text(original_cli_help)
    index = text_content.find('DESCRIPTION')
    if index > 0:
        text_content = text_content[index + len('DESCRIPTION'):]
    return text_content


def convert_rst_to_basic_text(contents):
    """Convert restructured text to basic text output.

    This function removes most of the decorations added
    in restructured text.

    This function is used to generate documentation we
    can show to users in a cross platform manner.

    Basic indentation and list formatting are kept,
    but many RST features are removed (such as
    section underlines).

    """
    # The report_level override is so that we don't print anything
    # to stdout/stderr on rendering issues.
    converted = publish_string(
        contents, writer=BasicTextWriter(),
        settings_overrides={'report_level': 5})
    return converted.decode('utf-8')


class FileRenderer(object):

    def __init__(self):
        self._io = BytesIO()

    def render(self, contents):
        self._io.write(contents)

    @property
    def contents(self):
        return self._io.getvalue()


class BasicTextWriter(textwriter.TextWriter):
    def translate(self):
        visitor = BasicTextTranslator(self.document)
        self.document.walkabout(visitor)
        self.output = visitor.body


class BasicTextTranslator(textwriter.TextTranslator):
    def depart_title(self, node):
        # Make the section titles upper cased, similar to
        # the man page output.
        text = ''.join(x[1] for x in self.states.pop() if x[0] == -1)
        self.stateindent.pop()
        self.states[-1].append((0, ['', text.upper(), '']))

    # The botocore TextWriter has additional formatting
    # for literals, for the aws-shell docs we don't want any
    # special processing so these nodes are noops.

    def visit_literal(self, node):
        pass

    def depart_literal(self, node):
        pass
