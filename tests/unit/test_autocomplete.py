import pytest
from awsshell.autocomplete import AWSCLIModelCompleter

@pytest.fixture
def index_data():
    return {
        'aws': {
            'arguments': [],
            'commands': [],
            'children': {},
        }
    }


def test_completes_service_names(index_data):
    index_data['aws']['commands'] = ['first', 'second']
    completer = AWSCLIModelCompleter(index_data)
    assert completer.autocomplete('fi') == ['first']


def test_completes_multiple_service_names(index_data):
    index_data['aws']['commands'] = ['abc', 'acd', 'b']
    completer = AWSCLIModelCompleter(index_data)
    assert completer.autocomplete('a') == ['abc', 'acd']


def test_no_completion(index_data):
    index_data['aws']['commands'] = ['foo', 'bar']
    completer = AWSCLIModelCompleter(index_data)
    assert completer.autocomplete('baz') == []


def test_can_complete_subcommands(index_data):
    index_data['aws']['commands'] = ['ec2']
    index_data['aws']['children'] = {
        'ec2': {
            'arguments': [],
            'commands': ['copy-image', 'copy-snapshot', 'other'],
            'children': {},
        }
    }
    completer = AWSCLIModelCompleter(index_data)
    # The completer tracks state to optimize lookups,
    # so we simulate exactly how it's called.
    completer.autocomplete('e')
    completer.autocomplete('ec')
    completer.autocomplete('ec2')
    completer.autocomplete('ec2 ')
    completer.autocomplete('ec2 c')
    completer.autocomplete('ec2 co')
    assert completer.autocomplete('ec2 cop') == ['copy-image', 'copy-snapshot']

def test_everything_completed_on_space(index_data):
    # Right after "aws ec2<space>" all the operations should be
    # autocompleted.
    index_data['aws']['commands'] = ['ec2']
    index_data['aws']['children'] = {
        'ec2': {
            'arguments': [],
            'commands': ['copy-image', 'copy-snapshot', 'other'],
            'children': {},
        }
    }
    completer = AWSCLIModelCompleter(index_data)
    completer.autocomplete('e')
    completer.autocomplete('ec')
    completer.autocomplete('ec2')
    assert completer.autocomplete('ec2 ') == ['copy-image', 'copy-snapshot',
                                              'other']


def test_autocomplete_top_leve_services_on_space(index_data):
    index_data['aws']['commands'] = ['first', 'second']
    completer = AWSCLIModelCompleter(index_data)
    assert completer.autocomplete(' ') == ['first', 'second']


def test_reset_auto_complete(index_data):
    index_data['aws']['commands'] = ['first', 'second']
    completer = AWSCLIModelCompleter(index_data)
    completer.autocomplete('f')
    completer.autocomplete('fi')
    completer.autocomplete('fir')
    # Then the user hits enter.
    # Now they've moved on to the next command.
    assert completer.autocomplete('d') == ['second']


def test_reset_after_subcommand_completion(index_data):
    index_data['aws']['commands'] = ['ec2', 's3']
    index_data['aws']['children'] = {
        'ec2': {
            'arguments': [],
            'commands': ['copy-image', 'copy-snapshot', 'other'],
            'children': {},
        }
    }
    completer = AWSCLIModelCompleter(index_data)
    # The completer tracks state to optimize lookups,
    # so we simulate exactly how it's called.
    completer.autocomplete('e')
    completer.autocomplete('ec')
    completer.autocomplete('ec2')
    completer.autocomplete('ec2 ')
    completer.autocomplete('ec2 c')
    completer.autocomplete('ec2 co')
    # The user hits enter and auto completes copy-snapshot.
    # The next request should be to auto complete
    # top level commands:
    assert completer.autocomplete('s') == ['s3']


def test_backspace_should_complete_previous_command(index_data):
    pass


def test_can_handle_entire_word_deleted(index_data):
    pass


def test_can_handle_entire_line_deleted(index_data):
    index_data['aws']['commands'] = ['ec2', 's3']
    index_data['aws']['children'] = {
        'ec2': {
            'arguments': [],
            'commands': ['copy-image', 'copy-snapshot', 'other'],
            'children': {},
        }
    }
    completer = AWSCLIModelCompleter(index_data)
    c = completer.autocomplete
    c('e')
    c('ec')
    c('ec2')
    c('ec2 ')
    c('ec2 c')
    c('ec2 co')
    # Use hits backspace a few times.
    c('ec2 c')
    c('ec2 ')
    c('ec2')
    # Now we should be auto completing 'ec2'
    assert c('ec') == ['ec2']


def test_autocompletes_argument_names(index_data):
    index_data['aws']['arguments'] = ['--query', '--debug']
    completer = AWSCLIModelCompleter(index_data)
    # These should only appear once in the output.  So we need
    # to know if we're a top level argument or not.
    assert completer.autocomplete('-') == ['--query', '--debug']
    assert completer.autocomplete('--q') == ['--query']


def test_autocompletes_global_and_service_args(index_data):
    index_data['aws']['arguments'] = ['--query', '--debug']
    index_data['aws']['commands'] = ['ec2']
    index_data['aws']['children'] = {
        'ec2': {
            'arguments': ['--query-ec2', '--instance-id'],
            'commands': [],
            'children': {},
        }
    }
    completer = AWSCLIModelCompleter(index_data)
    c = completer.autocomplete
    c('e')
    c('ec')
    c('ec2')
    c('ec2 ')
    c('ec2 -')
    c('ec2 --')
    assert c('ec2 --q') == ['--query', '--query-ec2']


def test_can_mix_options_and_commands(index_data):
    index_data['aws']['arguments'] = ['--no-validate-ssl']
    index_data['aws']['commands'] = ['ec2']
    index_data['aws']['children'] = {
        'ec2': {
            'argument_metadata': {},
            'arguments': ['--query-ec2', '--instance-id'],
            'commands': ['create-tags', 'describe-instances'],
            'children': {},
        }
    }
    completer = AWSCLIModelCompleter(index_data)
    c = completer.autocomplete
    partial_cmd = 'ec2 --no-validate-ssl'
    for i in range(1, len(partial_cmd)):
        c(partial_cmd[:i])

    assert c('ec2 --no-validate-ssl ') == ['create-tags', 'describe-instances']
    c('ec2 --no-validate-ssl c')
    c('ec2 --no-validate-ssl cr')
    c('ec2 --no-validate-ssl cre')
    c('ec2 --no-validate-ssl crea')
    assert c('ec2 --no-validate-ssl creat') == ['create-tags']


def test_only_change_context_when_in_index(index_data):
    index_data['aws']['arguments'] = ['--region']
    index_data['aws']['commands'] = ['ec2']
    index_data['aws']['children'] = {
        'ec2': {
            'commands': ['create-tags', 'describe-instances'],
            'children': {},
            'argument_metadata': {},
            'arguments': [],
        }
    }
    completer = AWSCLIModelCompleter(index_data)
    c = completer.autocomplete
    partial_cmd = 'ec2 --region us-west-2'
    for i in range(1, len(partial_cmd)):
        c(partial_cmd[:i])

    # We should ignore "us-west-2" because it's not a child
    # of ec2.
    assert c('ec2 --region us-west-2 ') == ['create-tags', 'describe-instances']


def test_can_handle_skips_in_completion(index_data):
    # Normally, completion is always requested char by char.
    # Typing "ec2 describe-inst"
    # will subsequent calls to the autocompleter:
    # 'e', 'ec', 'ec2', 'ec2 ', 'ec2 d', 'ec2 de' ... all the way
    # up to 'ec2 describe-inst'.
    # However, the autocompleter should gracefully handle when there's
    # skips, so two subsequent calls are 'ec' and then 'ec2 describe-ta',
    # the autocompleter should still do the right thing.  The tradeoff
    # will just be that this case will be slower than the common case
    # of char by char additions.
    index_data['aws']['commands'] = ['ec2']
    index_data['aws']['children'] = {
        'ec2': {
            'commands': ['create-tags', 'describe-instances'],
            'argument_metadata': {},
            'arguments': [],
            'children': {
                'create-tags': {
                    'argument_metadata': {
                        '--resources': {'example': '', 'minidoc': 'foo'},
                        '--tags': {'example': 'bar', 'minidoc': 'baz'},
                    },
                    'arguments': ['--resources', '--tags'],
                }
            },
        }
    }
    completer = AWSCLIModelCompleter(index_data)
    c = completer.autocomplete
    result = c('ec2 create-ta')
    assert result == ['create-tags']


def test_cmd_path_updated_on_completions(index_data):
    index_data['aws']['commands'] = ['ec2']
    index_data['aws']['children'] = {
        'ec2': {
            'commands': ['create-tags', 'describe-instances'],
            'argument_metadata': {},
            'arguments': [],
            'children': {
                'create-tags': {
                    'commands': [],
                    'argument_metadata': {
                        '--resources': {'example': '', 'minidoc': 'foo'},
                        '--tags': {'example': 'bar', 'minidoc': 'baz'},
                    },
                    'arguments': ['--resources', '--tags'],
                }
            }
        }
    }
    completer = AWSCLIModelCompleter(index_data)
    c = completer.autocomplete
    result = c('ec2 create-tags ')
    assert result == []
    assert completer.cmd_path == ['aws', 'ec2', 'create-tags']
    assert completer.arg_metadata == {
        '--resources': {'example': '', 'minidoc': 'foo'},
        '--tags': {'example': 'bar', 'minidoc': 'baz'},
    }


def test_last_option_updated_up_releated_api_params(index_data):
    index_data['aws']['commands'] = ['ec2']
    index_data['aws']['children'] = {
        'ec2': {
            'commands': ['create-tags'],
            'argument_metadata': {},
            'arguments': [],
            'children': {
                'create-tags': {
                    'commands': [],
                    'argument_metadata': {
                        '--resources': {'example': '', 'minidoc': 'foo'},
                        '--tags': {'example': 'bar', 'minidoc': 'baz'},
                    },
                    'arguments': ['--resources', '--tags'],
                    'children': {},
                }
            }
        }
    }
    completer = AWSCLIModelCompleter(index_data)
    completer.autocomplete('ec2 create-tags --resources ')
    assert completer.last_option == '--resources'
    completer.autocomplete('ec2 create-tags --resources f --tags ')
    # last_option should be updated.
    assert completer.last_option == '--tags'


def test_last_option_is_updated_on_global_options(index_data):
    index_data['aws']['arguments'] = ['--no-sign-request']
    index_data['aws']['commands'] = ['ec2']
    index_data['aws']['children'] = {
        'ec2': {
            'commands': ['create-tags'],
            'argument_metadata': {},
            'arguments': [],
            'children': {
                'create-tags': {
                    'commands': [],
                    'argument_metadata': {
                        '--resources': {'example': '', 'minidoc': 'foo'},
                    },
                    'arguments': ['--resources'],
                    'children': {},
                }
            }
        }
    }
    completer = AWSCLIModelCompleter(index_data)
    completer.autocomplete('ec2 create-tags --resources ')
    assert completer.last_option == '--resources'
    completer.autocomplete('ec2 create-tags --resources f --no-sign-request ')
    assert completer.last_option == '--no-sign-request'


def test_can_handle_autocompleting_same_string_twice(index_data):
    index_data['aws']['commands'] = ['first', 'second']
    completer = AWSCLIModelCompleter(index_data)
    completer.autocomplete('f')
    assert completer.autocomplete('f') == ['first']


def test_can_handle_autocomplete_empty_string_twice(index_data):
    # Sometimes prompt_toolkit will try to autocomplete
    # the empty string multiple times.  We need to handle this
    # gracefully.
    index_data['aws']['commands'] = ['first', 'second']
    completer = AWSCLIModelCompleter(index_data)
    assert completer.autocomplete('') == []
    assert completer.autocomplete('') == []
