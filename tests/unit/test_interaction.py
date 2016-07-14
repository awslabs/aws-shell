import mock
import pytest

from awsshell.interaction import InteractionLoader, InteractionException
from awsshell.interaction import SimpleSelect, SimplePrompt


@pytest.fixture
def loader():
    return InteractionLoader()


@pytest.fixture
def simple_selector():
    model = {'Path': '[].a'}
    return SimpleSelect(model, 'Promptingu')


@pytest.fixture
def simple_prompt():
    return SimplePrompt({}, 'Prompt yo')


def test_loader(loader):
    # Verify the interaction loader instantiates the correct object
    instance = loader.create({'ScreenType': 'SimpleSelect'}, 'Prompt')
    assert isinstance(instance, SimpleSelect)


def test_loader_invalid_types(loader):
    # Verify that the loader throws exceptions for invalid screen types
    with pytest.raises(InteractionException) as ie:
        loader.create({'ScreenType': 'NotReal'}, 'Prompt')
    assert 'Invalid interaction type: NotReal' in str(ie.value)
    with pytest.raises(InteractionException) as ie:
        loader.create({'ScreenType': 'InteractionLoader'}, 'Prompt')
    assert 'Invalid interaction type: InteractionLoader' in str(ie.value)


def test_simple_select():
    # Verify that SimpleSelect calls prompt and it returns a selection
    prompt = mock.Mock()
    selector = SimpleSelect({}, 'one or two?', prompt)
    options = ['one', 'two']
    prompt.return_value = options[1]
    xformed = selector.execute(options)
    assert prompt.call_count == 1
    assert xformed == options[1]


def test_simple_select_with_path():
    # Verify that SimpleSelect calls prompt and it returns the corresponding
    # item derived from the path.
    prompt = mock.Mock()
    model = {'Path': '[].a'}
    simple_selector = SimpleSelect(model, 'Promptingu', prompt)
    options = [{'a': '1', 'b': 'one'}, {'a': '2', 'b': 'two'}]
    prompt.return_value = '2'
    xformed = simple_selector.execute(options)
    assert prompt.call_count == 1
    assert xformed == options[1]


def test_simple_select_bad_data(simple_selector):
    # Test that simple select throws exceptions when given bad data
    with pytest.raises(InteractionException) as ie:
        simple_selector.execute({})
    assert 'SimpleSelect expects a non-empty list' in str(ie.value)
    with pytest.raises(InteractionException) as ie:
        simple_selector.execute([])
    assert 'SimpleSelect expects a non-empty list' in str(ie.value)


def test_simple_prompt():
    # Verify that simple prompt calls prompt with correct args and that the
    # resulting dict is filled out accordingly.
    prompt = mock.Mock()
    simple_prompt = SimplePrompt({}, 'Prompt yo', prompt)
    fields = {'a': '', 'b': '', 'c': ''}
    prompt.return_value = 'input'
    xformed = simple_prompt.execute(fields)
    calls = [mock.call('a: '), mock.call('b: '), mock.call('c: ')]
    prompt.assert_has_calls(calls, any_order=True)
    assert xformed == {'a': 'input', 'b': 'input', 'c': 'input'}


def test_simple_prompt_bad_data(simple_prompt):
    # Test that simple prompt raises exceptions when data is not a dict
    with pytest.raises(InteractionException) as ie:
        simple_prompt.execute([])
    assert 'SimplePrompt expects a dict as data' in str(ie.value)
