from awsshell import db
import pytest


@pytest.fixture
def shell_db(tmpdir):
    filename = tmpdir.join('docs.db').strpath
    d = db.ConcurrentDBM.create(filename)
    return d


def test_can_get_and_set_value(shell_db):
    shell_db['foo'] = 'bar'
    assert shell_db['foo'] == 'bar'


def test_raise_key_error_when_no_key_exists(shell_db):
    try:
        shell_db['foo']
    except KeyError as e:
        assert 'foo' in str(e)
    else:
        raise AssertionError("Expected KeyError")


def test_can_set_multiple_values(shell_db):
    shell_db['foo'] = 'a'
    shell_db['bar'] = 'b'
    assert shell_db['foo'] == 'a'
    assert shell_db['bar'] == 'b'


def test_can_change_existing_value(shell_db):
    shell_db['foo'] = 'first'
    shell_db['foo'] = 'second'
    assert shell_db['foo'] == 'second'


def test_can_update_multiple_times(shell_db):
    for i in range(100):
        shell_db['foo'] = str(i)
    assert shell_db['foo'] == '99'


def test_can_handle_unicode(shell_db):
    shell_db['foo'] = u'\u2713'
    assert shell_db['foo'] == u'\u2713'


def test_can_create_and_open_db(tmpdir):
    filename = tmpdir.join('foo.db').strpath
    d = db.ConcurrentDBM.create(filename)
    d['foo'] = 'bar'
    d.close()

    # Should be able to reopen the database and look up 'foo'.
    d = db.ConcurrentDBM.open(filename)
    assert d['foo'] == 'bar'
