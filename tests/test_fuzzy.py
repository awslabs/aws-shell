import pytest
from awsshell.fuzzy import fuzzy_search


@pytest.mark.parametrize("search,corpus,expected", [
    ('foo', ['foobar', 'foobaz'], ['foobar', 'foobaz']),
    ('f', ['foo', 'foobar', 'bar'], ['foo', 'foobar']),
    ('fbb', ['foo-bar-baz', 'fo-ba-baz', 'bar'], ['foo-bar-baz', 'fo-ba-baz']),
    ('fff', ['fi-fi-fi', 'fo'], ['fi-fi-fi']),
    # The more chars it matches, the higher the score.
    ('pre', ['prefix', 'pre', 'not'], ['pre', 'prefix']),
    ('nomatch', ['noma', 'nomatccc'], []),
])
def test_subsequences(search, corpus, expected):
    actual = fuzzy_search(search, corpus)
    assert actual == expected
