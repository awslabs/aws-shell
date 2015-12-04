from awsshell import docs
from awsshell import db


def test_lazy_doc_factory(tmpdir):
    filename = tmpdir.join('foo.db').strpath
    doc_index = docs.load_lazy_doc_index(filename)
    assert isinstance(doc_index, docs.DocRetriever)


def test_load_doc_db(tmpdir):
    filename = tmpdir.join("foo.db").strpath
    d = docs.load_doc_db(filename)
    assert isinstance(d, db.ConcurrentDBM)
