import mock
import pytest

from prompt_toolkit.token import Token
from awsshell.selectmenu import select_prompt, SelectMenuControl, \
    SelectMenuApplication


@pytest.fixture
def menu_control():
    options = [u'option 1', u'opt 2', u'option 3']
    return SelectMenuControl(options)


def test_select_prompt_creation():
    # Test that the runner is given a select menu application
    mock_runner = mock.Mock()
    select_prompt(u'Prompt: ', [u'option'], runner=mock_runner)
    assert mock_runner.call_count == 1
    (args, kwargs) = mock_runner.call_args
    assert isinstance(args[0], SelectMenuApplication)


def test_select_menu_control_width(menu_control):
    # Width should be longest option plus 2
    dummy = mock.Mock()
    assert menu_control.preferred_width(dummy, dummy) == len('option 1') + 2


def test_select_menu_control_width_min():
    # Width should be at least the minimum
    menu_control = SelectMenuControl([u''])
    dummy = mock.Mock()
    assert menu_control.preferred_width(dummy, dummy) == menu_control.MIN_WIDTH


def test_select_menu_control_height(menu_control):
    # Height should be the number of options
    dummy = mock.Mock()
    height = menu_control.preferred_height(dummy, dummy, dummy, dummy)
    assert height == 3


def test_select_menu_get_selection(menu_control):
    # Test that get selection returns the correct option
    assert menu_control.get_selection() is None
    menu_control.select_down()
    assert menu_control.get_selection() == 'option 1'
    menu_control.select_down()
    assert menu_control.get_selection() == 'opt 2'
    menu_control.select_up()
    assert menu_control.get_selection() == 'option 1'


def test_select_menu_get_select_down(menu_control):
    # Test that select down wraps around correctly
    assert menu_control.get_selection() is None
    menu_control.select_down()
    assert menu_control.get_selection() == 'option 1'
    menu_control.select_down()
    assert menu_control.get_selection() == 'opt 2'
    menu_control.select_down()
    assert menu_control.get_selection() == 'option 3'
    menu_control.select_down()
    assert menu_control.get_selection() == 'option 1'


def test_select_menu_get_select_up(menu_control):
    # Test that select up wraps around correctly
    assert menu_control.get_selection() is None
    menu_control.select_up()
    assert menu_control.get_selection() == 'option 3'
    menu_control.select_up()
    assert menu_control.get_selection() == 'opt 2'
    menu_control.select_up()
    assert menu_control.get_selection() == 'option 1'
    menu_control.select_up()
    assert menu_control.get_selection() == 'option 3'


def test_select_menu_inserts_text(menu_control):
    # Test that selection will modify the current buffer if given an event
    mock_event = mock.Mock()
    menu_control.select_down(event=mock_event)
    assert mock_event.current_buffer.document.text == 'option 1'
    menu_control.select_up(event=mock_event)
    assert mock_event.current_buffer.document.text == 'option 3'


def test_select_menu_create_content(menu_control):
    dummy = mock.Mock()
    ui_content = menu_control.create_content(dummy, dummy, dummy)
    # assert the generated get line is callable
    assert callable(ui_content.get_line)
    get_line = ui_content.get_line
    token = Token.Menu.Completions
    # assert the correct lines and tokens are generated
    assert [(token.Completion, ' option 1   ')] == get_line(0)
    assert [(token.Completion, ' opt 2      ')] == get_line(1)
    assert [(token.Completion, ' option 3   ')] == get_line(2)
    menu_control.select_down()
    assert [(token.Completion.Current, ' option 1   ')] == get_line(0)
    assert [(token.Completion, ' opt 2      ')] == get_line(1)
    assert [(token.Completion, ' option 3   ')] == get_line(2)
    menu_control.select_down()
    assert [(token.Completion, ' option 1   ')] == get_line(0)
    assert [(token.Completion.Current, ' opt 2      ')] == get_line(1)
    assert [(token.Completion, ' option 3   ')] == get_line(2)
