import threading

from awsshell import compat
from awsshell import db


def load_lazy_doc_index(filename):
    d = load_doc_db(filename)
    return DocRetriever(d)


def load_doc_db(filename):
    d = db.ConcurrentDBM.open(filename, create=True)
    return d


class DocRetriever(object):
    """Retrieves documentation for the AWS CLI.
    """
    def __init__(self, doc_index):
        # Internally, most of the speedup comes from
        # the fact that this data is pre-rendered and
        # indexed.
        self._doc_index = doc_index
        self._cache = {}

    def extract_description(self, dot_cmd):
        try:
            docs = self._doc_index[dot_cmd]
        except KeyError:
            return u''
        docs = docs.decode('utf-8')
        index = docs.find('SYNOPSIS')
        if index > 0:
            docs = docs[:index]
        return docs

    def extract_param(self, dot_cmd, param_name):
        try:
            docs = self._doc_index[dot_cmd]
        except KeyError:
            return u''
        docs = docs.decode('utf-8')
        index = docs.find('OPTIONS')
        param_start_index = docs.find(param_name, index)
        param_end_index = docs.find('  --', param_start_index)
        return docs[param_start_index:param_end_index]
