import pytest
import mock


from awsshell import app
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


def test_prints_error_message_on_unknown_dot_command(errstream):
    handler = app.DotCommandHandler(err=errstream)
    handler.handle_cmd(".unknown foo bar", None)
    assert errstream.getvalue() == "Unknown dot command: .unknown\n"
