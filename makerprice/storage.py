"""Local SQLite library and atomic JSON documents; no cloud or network dependency."""
import json
import os
from pathlib import Path
import sqlite3
import tempfile
from datetime import datetime, timezone
from .domain import Quote


def write_document(path, quote):
    data = json.dumps(quote.document(), ensure_ascii=False, indent=2)
    path = Path(path)
    tmp = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent,
                                         prefix='.makerprice-', delete=False) as stream:
            tmp = stream.name
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(tmp, path)
    finally:
        if tmp and os.path.exists(tmp):
            os.unlink(tmp)


def read_document(path):
    if Path(path).stat().st_size > 2_000_000:
        raise ValueError('O arquivo é muito grande para um orçamento.')
    with open(path, encoding='utf-8') as stream:
        return Quote.from_document(json.load(stream))


class Library:
    def __init__(self, path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path)
        self.db.execute('CREATE TABLE IF NOT EXISTS quotes (id INTEGER PRIMARY KEY, title TEXT, client TEXT, updated TEXT, payload TEXT)')
        self.db.execute('CREATE TABLE IF NOT EXISTS profiles (kind TEXT, name TEXT, payload TEXT, PRIMARY KEY(kind, name))')
        self.db.commit()

    def save(self, quote, identity=None):
        payload = json.dumps(quote.document(), ensure_ascii=False)
        values = (quote.title, quote.client, datetime.now(timezone.utc).isoformat(), payload)
        with self.db:
            if identity is None:
                return self.db.execute('INSERT INTO quotes(title,client,updated,payload) VALUES (?,?,?,?)', values).lastrowid
            self.db.execute('UPDATE quotes SET title=?,client=?,updated=?,payload=? WHERE id=?', (*values, identity))
        return identity

    def list(self, query=''):
        return self.db.execute('SELECT id,title,client,updated FROM quotes WHERE title LIKE ? OR client LIKE ? ORDER BY updated DESC',
                               (f'%{query}%', f'%{query}%')).fetchall()

    def get(self, identity):
        row = self.db.execute('SELECT payload FROM quotes WHERE id=?', (identity,)).fetchone()
        if not row:
            raise ValueError('Orçamento não encontrado.')
        return Quote.from_document(json.loads(row[0]))

    def profiles(self, kind):
        return [(name, json.loads(payload)) for name, payload in self.db.execute(
            'SELECT name,payload FROM profiles WHERE kind=? ORDER BY name', (kind,))]

    def save_profile(self, kind, name, payload):
        with self.db:
            self.db.execute('INSERT OR REPLACE INTO profiles VALUES (?,?,?)', (kind, name, json.dumps(payload)))

    def close(self):
        self.db.close()
