import json
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from contextlib import closing
from unittest.mock import patch
from analysis import engine, web_engine
from scripts.prepare_anonymous import build


class PrivacyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.old = engine.ROOT
        engine.ROOT = self.root
        with closing(engine.db()) as con:
            for kind in ('stock', 'movement'):
                con.execute('INSERT INTO batches VALUES(?,?,?,?,?,?,?,?,?,?)',
                    (kind, kind, kind, 'PRIVATE_FILE.csv', '2024-12-30', 1, 1, 0, '2024-12-30', '{}'))
                row = {'Kodu': 'SECRET-PRODUCT', 'Malzeme Kodu': 'SECRET-PRODUCT',
                       'Aciklamasi': 'SECRET PRODUCT NAME', 'Malzeme Aciklamasi': 'SECRET PRODUCT NAME',
                       'Müsteri Kodu': 'SECRET-CUSTOMER', 'Müsteri Ünvani': 'SECRET CUSTOMER NAME',
                       'Fatura No': 'SECRET-INVOICE', 'Fatura Türü': 'Satış Faturası',
                       'Fatura Tarihi': '2020-02-03', 'Miktar': '987654', 'Stok Miktari': '987654',
                       'Net Satir Tutari': '987654321', 'Sevkiyat Adresi': 'SECRET ADDRESS',
                       'Satici': 'SECRET SELLER', 'Ambar': 'SECRET WAREHOUSE', 'Malzeme Grubu': 'SECRET GROUP',
                       'extra_note': 'SECRET UNKNOWN FIELD'}
                con.execute('INSERT INTO records(batch_id,source_line,kind,fingerprint,raw,converted) VALUES(?,?,?,?,?,?)',
                            (kind, 2, kind, kind, json.dumps(row), json.dumps(row)))
            con.execute("INSERT INTO actions(id,entity_type,entity_id,title,description,priority,status,owner,created,updated) VALUES('old','product','x','SECRET ACTION','SECRET NOTE','high','open','SECRET OWNER','2024-01-01','2024-01-01')")
            con.commit()
        self.original = (self.root / 'center.sqlite').read_bytes()

    def tearDown(self):
        engine.ROOT = self.old
        self.temp.cleanup()

    def test_separate_copy_scrubs_all_artifacts_and_preserves_original(self):
        destination = self.root / 'anonymous'
        self.assertEqual(build(self.root, destination), {'stock': 1, 'movement': 1})
        self.assertEqual(self.original, (self.root / 'center.sqlite').read_bytes())
        for p in destination.rglob('*'):
            if p.is_file():
                content = p.read_bytes()
                for token in (b'SECRET', b'PRIVATE_FILE', b'987654', b'2020-02-03'):
                    self.assertNotIn(token, content, str(p))
        with closing(sqlite3.connect(destination / 'center.sqlite')) as con:
            rows = [json.loads(r[0]) for r in con.execute('SELECT converted FROM records ORDER BY kind')]
            self.assertEqual(rows[0]['Malzeme Kodu'], rows[1]['Kodu'])
            self.assertEqual(con.execute('SELECT count(*) FROM actions').fetchone()[0], 0)
        with self.assertRaises(ValueError):
            build(self.root, destination)
        with self.assertRaises(ValueError):
            build(self.root, self.root)

    def test_web_default_never_reads_original_and_blocks_ingestion(self):
        with patch.dict(os.environ, {'DATA_DIR': str(self.root), 'APP_DATA_MODE': 'anonymous'}):
            self.assertEqual(web_engine.dispatch({'action': 'list'})['batches'], [])
            for action in ('inspect', 'analyze', 'commit'):
                with self.assertRaises(ValueError):
                    web_engine.dispatch({'action': action})
            self.assertEqual(self.original, (self.root / 'center.sqlite').read_bytes())

    def test_invalid_mode_fails_closed(self):
        with patch.dict(os.environ, {'DATA_DIR': str(self.root), 'APP_DATA_MODE': 'typo'}):
            web_engine.dispatch({'action': 'schema'})
            self.assertEqual(engine.ROOT, self.root / 'anonymous')


if __name__ == '__main__':
    unittest.main()
