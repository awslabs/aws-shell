import mock
import pytest

from prompt_toolkit.keys import Keys
from prompt_toolkit.token import Token
from prompt_toolkit.document import Document
from prompt_toolkit.enums import DEFAULT_BUFFER
from prompt_toolkit.shortcuts import create_eventloop
from prompt_toolkit.interface import CommandLineInterface
from prompt_toolkit.key_binding.input_processor import KeyPress

from awsshell.selectmenu import SelectMenuApplication


@pytest.fixture
def cli():
    app = SelectMenuApplication(u'prompt', [u'1', u'2', u'3'])
    return CommandLineInterface(application=app, eventloop=create_eventloop())


def feed_key(cli, key, data=u''):
    cli.input_processor.feed(KeyPress(key, data))
    cli.input_processor.process_keys()


def test_select_menu_layout(cli):
    layout = cli.application.layout
    prompt_window = layout.children[0].content.children[0]
    buffer_control = prompt_window.content
    get_tokens = buffer_control.input_processors[0].get_tokens
    assert callable(get_tokens)
    assert get_tokens(mock.Mock) == [(Token.Prompt, 'prompt')]
    height = prompt_window.preferred_height(cli, 100, 20)
    # assert that the menu reserves space
    assert height.min == height.preferred == 8
    cli.set_exit()
    height = prompt_window.preferred_height(cli, 100, 20)
    # assert that menu doesn't take up space when cli is exiting
    assert height.min == 0
    assert height.preferred == 1


def test_select_menu_application_f10(cli):
    feed_key(cli, Keys.F10)
    assert cli.is_exiting


@pytest.mark.parametrize('key', [Keys.Up, Keys.BackTab])
def test_select_menu_application_up_backtab(cli, key):
    feed_key(cli, key)
    assert cli.application.menu_control.get_selection() == '3'


@pytest.mark.parametrize('key', [Keys.Down, Keys.Tab])
def test_select_menu_application_down_tab(cli, key):
    feed_key(cli, key)
    assert cli.application.menu_control.get_selection() == '1'


def test_select_menu_application_accept(cli):
    feed_key(cli, Keys.ControlJ)
    # assert that no selection fails to accept
    assert cli.return_value() is None
    # move selection down then accept
    feed_key(cli, Keys.Down)
    feed_key(cli, Keys.ControlJ)
    assert cli.return_value() == ('1', 0)


def test_select_menu_application_any(cli):
    buf = cli.application.buffers[DEFAULT_BUFFER]
    # assert typing doesn't add text
    feed_key(cli, Keys.Any, data=u'abc')
    assert buf.text == ''
    buf.document = Document(u'abc')
    # assert backspace doesn't remove text
    feed_key(cli, Keys.Backspace)
    assert buf.text == 'abc'


def test_select_menu_application_with_meta():
    # test that selecting an option when theres info will render it
    meta = [{'key': u'val'}]
    app = SelectMenuApplication(u'prompt', [u'opt'], options_meta=meta)
    cli = CommandLineInterface(application=app, eventloop=create_eventloop())
    feed_key(cli, Keys.Down)
    assert cli.application.buffers['INFO'].text == '{\n    "key": "val"\n}'


def test_select_menu_duplicate_option_with_meta():
    options = [u'one', u'one']
    meta = [{'key': u'1'}, {'key': u'2'}]
    app = SelectMenuApplication(u'prompt', options, options_meta=meta)
    cli = CommandLineInterface(application=app, eventloop=create_eventloop())
    feed_key(cli, Keys.Down)
    assert cli.application.buffers['INFO'].text == '{\n    "key": "1"\n}'
    feed_key(cli, Keys.ControlJ)
    assert cli.return_value() == ('one', 0)
    feed_key(cli, Keys.Down)
    assert cli.application.buffers['INFO'].text == '{\n    "key": "2"\n}'
    feed_key(cli, Keys.ControlJ)
    assert cli.return_value() == ('one', 1)
