import pytest
import mock


from awsshell import app
from awsshell import shellcomplete
from awsshell import compat


@pytest.fixture
def errstream():
    return compat.StringIO()


def test_can_dispatch_dot_commands():
    call_args = []
    class CustomHandler(object):
        def run(self, command, context):
            call_args.append((command, context))
    handler = app.DotCommandHandler()
    handler.HANDLER_CLASSES['foo'] = CustomHandler
    context = object()

    handler.handle_cmd('.foo a b c', context)

    assert call_args == [(['.foo', 'a', 'b', 'c'], context)]


def test_edit_handler():
    env = {'EDITOR': 'my-editor'}
    popen_cls = mock.Mock()
    context = mock.Mock()
    context.history = []
    handler = app.EditHandler(popen_cls, env)
    handler.run(['.edit'], context)
    # Ensure our editor was called with some arbitrary temp filename.
    command_run = popen_cls.call_args[0][0]
    assert len(command_run) == 2
    assert command_run[0] == 'my-editor'


def test_error_msg_printed_on_error_handler(errstream):
    env = {'EDITOR': 'my-editor'}
    popen_cls = mock.Mock()
    popen_cls.side_effect = OSError()
    context = mock.Mock()
    context.history = []
    handler = app.EditHandler(popen_cls, env, errstream)
    handler.run(['.edit'], context)

    # Then we should not propagate an exception, and we
    # should print a helpful error message.
    assert 'Unable to launch editor: my-editor' in errstream.getvalue()


def test_profile_handler_prints_profile():
    shell = mock.Mock(spec=app.AWSShell)
    shell.profile = 'myprofile'
    stdout = compat.StringIO()
    handler = app.ProfileHandler(stdout)
    handler.run(['.profile'], shell)
    assert stdout.getvalue().strip() == 'Current shell profile: myprofile'


def test_profile_handler_when_no_profile_configured():
    shell = mock.Mock(spec=app.AWSShell)
    shell.profile = None
    stdout = compat.StringIO()
    handler = app.ProfileHandler(stdout)
    handler.run(['.profile'], shell)
    assert stdout.getvalue() == (
        'Current shell profile: no profile configured\n'
        'You can change profiles using: .profile profile-name\n'
    )


def test_profile_command_changes_profile():
    shell = mock.Mock(spec=app.AWSShell)
    shell.profile = 'myprofile'
    stdout = compat.StringIO()
    handler = app.ProfileHandler(stdout)

    handler.run(['.profile', 'newprofile'], shell)

    assert shell.profile == 'newprofile'


def test_profile_prints_error_on_bad_syntax():
    stderr = compat.StringIO()
    handler = app.ProfileHandler(None, stderr)
    handler.run(['.profile', 'a', 'b', 'c'], None)

    # We don't really care about the exact usage message here,
    # we just want to ensure usage was written to stderr.
    assert 'Usage' in stderr.getvalue()


def test_prints_error_message_on_unknown_dot_command(errstream):
    handler = app.DotCommandHandler(err=errstream)
    handler.handle_cmd(".unknown foo bar", None)
    assert errstream.getvalue() == "Unknown dot command: .unknown\n"


def test_delegates_to_complete_changing_profile():
    completer = mock.Mock(spec=shellcomplete.AWSShellCompleter)
    shell = app.AWSShell(completer, mock.Mock(), mock.Mock())
    shell.profile = 'mynewprofile'
    assert completer.change_profile.call_args == mock.call('mynewprofile')
    assert shell.profile == 'mynewprofile'


def test_cd_handler_can_chdir():
    chdir = mock.Mock()
    handler = app.ChangeDirHandler(chdir=chdir)
    handler.run(['.cd', 'foo/bar'], None)
    assert chdir.call_args == mock.call('foo/bar')


def test_chdir_syntax_error_prints_err_msg(errstream):
    chdir = mock.Mock()
    handler = app.ChangeDirHandler(err=errstream, chdir=chdir)
    handler.run(['.cd'], None)
    assert 'invalid syntax' in errstream.getvalue()
    assert not chdir.called


def test_error_displayed_when_chdir_fails(errstream):
    chdir = mock.Mock()
    chdir.side_effect = OSError("FAILED")
    handler = app.ChangeDirHandler(err=errstream, chdir=chdir)
    handler.run(['.cd', 'foo'], None)
    assert 'FAILED' in errstream.getvalue()


def test_exit_dot_command_exits_shell():
    mock_prompter = mock.Mock()
    # Simulate the user entering '.quit'
    fake_document = mock.Mock()
    fake_document.text = '.quit'
    mock_prompter.run.return_value = fake_document
    shell = app.AWSShell(mock.Mock(), mock.Mock(), mock.Mock())
    shell.create_cli_interface = mock.Mock(return_value=mock_prompter)
    shell.run()

    # Should have only called run() once.  As soon as we
    # see the .quit command, we immediately exit and stop prompting
    # for more shell commands.
    assert mock_prompter.run.call_count == 1
