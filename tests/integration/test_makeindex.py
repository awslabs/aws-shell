import awscli.clidriver
from awsshell import makeindex

import pytest


@pytest.fixture
def cloudformation_command():
    driver = awscli.clidriver.create_clidriver()
    cmd = driver.create_help_command()
    cfn = cmd.command_table['cloudformation']
    return cfn


def test_can_write_doc_index_for_single_operation(cloudformation_command):
    # We don't want to try to generate the entire doc index
    # for all commands.  We're just trying to ensure we're
    # integrating with the AWS CLi's help commands properly
    # so we're going to pick a single operation to document.
    create_stack = cloudformation_command.create_help_command()\
            .command_table['create-stack']
    help_command = create_stack.create_help_command()
    rendered = makeindex.render_docs_for_cmd(help_command=help_command)
    # We *really* don't want these to fail when the wording
    # changes so I'm purposefully not picking long phrases.
    assert 'Creates a stack' in rendered
    # Should also see sections in the rendered content.
    assert 'SYNOPSIS' in rendered
    assert 'EXAMPLES' in rendered
    assert 'OUTPUT' in rendered
    # Should also see a parameter.
    assert '--stack-name' in rendered


def test_can_document_all_service_commands(cloudformation_command):
    db = {}
    help_command = cloudformation_command.create_help_command()
    makeindex.write_doc_index(db=db, help_command=help_command)
    # Again, we don't want these to fail when cloudformation has
    # API updates so I don't have very strict checking.
    assert 'aws.cloudformation.create-stack' in db
    assert 'aws.cloudformation.delete-stack' in db
    assert 'SYNOPSIS' in db['aws.cloudformation.create-stack']


def test_can_index_a_command(cloudformation_command):
    help_command = cloudformation_command.create_help_command()
    index = makeindex.new_index()
    makeindex.index_command(index, help_command)
