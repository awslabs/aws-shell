from __future__ import unicode_literals
import os
import sqlite3


class ConcurrentDBM(object):

    @classmethod
    def open(cls, filename, create=False):
        if create and not os.path.isfile(filename):
            return cls.create(filename)
        else:
            db = sqlite3.connect(filename)
            return cls(db)

    @classmethod
    def create(cls, filename):
        db = sqlite3.connect(filename)
        with db:
            db.execute(
                'CREATE TABLE docindex (key TEXT PRIMARY KEY, value TEXT)')
        return cls(db)

    def __init__(self, db):
        self._db = db

    def __getitem__(self, key):
        if isinstance(key, bytes):
            key = key.decode('utf-8')
        cursor = self._db.cursor()
        cursor.execute(
            'SELECT value FROM docindex WHERE key = :key', {'key': key})
        result = cursor.fetchone()
        if result is not None:
            return result[0]
        raise KeyError(key)

    def __setitem__(self, key, value):
        with self._db:
            self._db.execute(
                'INSERT OR REPLACE INTO docindex (key, value) '
                'VALUES (:key, :value)',
                {'key': key, 'value': value})

    def close(self):
        self._db.close()
