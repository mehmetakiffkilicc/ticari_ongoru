import json
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

from analysis import engine
from analysis import decision_workflow as workflow


class DecisionWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.old_root = engine.ROOT
        engine.ROOT = Path(self.temp.name)
        self.signal = {'id':'signal-1','module':'customers','entityType':'customer','entityId':'C1','entityName':'Müşteri Bir',
          'code':'CUSTOMER_LOSS_RISK','title':'Kayıp riski','severity':'critical','score':88,'confidence':'Yüksek',
          'impact':1200,'evidence':{'observed':130,'threshold':90,'impact':1200},'recommendedAction':'Müşteriyle temas kurun.'}

    def tearDown(self):
        engine.ROOT = self.old_root
        self.temp.cleanup()

    def sync(self, day='2024-12-30', signals=None):
        with patch.object(workflow, '_collect', return_value=(day, self.signal if False else (signals if signals is not None else [self.signal]))):
            return workflow.synchronize({})

    def seed_source(self):
        rows = [
          {'Fatura Türü':'Satış Faturası','Fatura Tarihi':'2024-12-20','Fatura No':'S-101','Müsteri Kodu':'C1','Malzeme Kodu':'P1','Satici':'Ayşe','Net Satir Tutari':'125.50'},
          {'Fatura Türü':'Satın Alma Faturası','Fatura Tarihi':'2024-12-21','Fatura No':'P-999','Müsteri Kodu':'C1','Malzeme Kodu':'P1','Satici':'Ayşe','Net Satir Tutari':'9999'},
        ]
        with closing(engine.db()) as con:
            con.execute("INSERT INTO batches(id,kind,digest,name,created,rows,accepted,rejected,snapshot,report) VALUES(?,?,?,?,?,?,?,?,?,?)",
                        ('source-batch','movement','source-digest','hareket.csv','2024-12-30T10:00:00',2,2,0,'2024-12-30','{}'))
            for index, row in enumerate(rows, 7):
                con.execute("INSERT INTO records(batch_id,source_line,kind,fingerprint,raw,converted) VALUES(?,?,?,?,?,?)",
                            ('source-batch',index,'movement',f'source-{index}',json.dumps(row),json.dumps(row)))
            con.commit()

    def test_unified_signal_is_deduplicated_and_tracks_occurrence(self):
        self.sync(); self.sync()
        with closing(engine.db()) as con:
            self.assertEqual(con.execute('SELECT COUNT(*) FROM signal_instances').fetchone()[0], 1)
            self.assertEqual(con.execute('SELECT COUNT(*) FROM signal_occurrences').fetchone()[0], 1)
            meta = con.execute('SELECT lifecycle,occurrence_count FROM signal_metadata').fetchone()
            self.assertEqual((meta['lifecycle'], meta['occurrence_count']), ('new', 1))
        self.sync('2025-01-01')
        with closing(engine.db()) as con:
            meta = con.execute('SELECT lifecycle,occurrence_count FROM signal_metadata').fetchone()
            self.assertEqual((meta['lifecycle'], meta['occurrence_count']), ('recurring', 2))

    def test_false_positive_requires_reason_and_closes_alert(self):
        self.sync()
        with self.assertRaises(ValueError):
            workflow.review_signal({'signalId':'signal-1','disposition':'false_positive','note':'yok'})
        workflow.review_signal({'signalId':'signal-1','disposition':'false_positive','note':'Kaynak kaydı mükerrer işlendi.'})
        with closing(engine.db()) as con:
            self.assertEqual(con.execute('SELECT disposition FROM signal_metadata').fetchone()[0], 'false_positive')
            self.assertEqual(con.execute('SELECT status FROM alerts').fetchone()[0], 'resolved')
        self.sync()
        with closing(engine.db()) as con:
            self.assertEqual(con.execute('SELECT status FROM alerts').fetchone()[0], 'resolved')

    def test_action_closure_records_outcome_impact_and_cycle(self):
        self.sync()
        action = engine.action_create({'signalId':'signal-1','dueDate':'2024-12-31'})
        workflow.update_action({'id':action['id'],'status':'in_progress'})
        workflow.update_action({'id':action['id'],'status':'completed','outcome':'converted','realizedImpact':'500','note':'Sipariş alındı.'})
        with closing(engine.db()) as con:
            closure = con.execute('SELECT * FROM action_closures WHERE action_id=?',(action['id'],)).fetchone()
            self.assertEqual(closure['outcome'], 'converted')
            self.assertEqual(closure['realized_impact'], 500)
            self.assertEqual(closure['closure_note'], 'Sipariş alındı.')
            self.assertGreaterEqual(closure['cycle_hours'], 0)

    def test_center_reports_overdue_conversion_impact_and_review_metrics(self):
        self.sync()
        workflow.review_signal({'signalId':'signal-1','disposition':'confirmed','note':'Kanıt doğrulandı.'})
        first = engine.action_create({'signalId':'signal-1','dueDate':'2020-01-01'})
        workflow.update_action({'id':first['id'],'status':'completed','outcome':'converted','realizedImpact':750,'note':'Tamamlandı.'})
        with patch.object(workflow, 'synchronize', return_value={'status':'ready','analysisDate':'2024-12-30','signals':1}):
            center = workflow.unified_center({})
        self.assertEqual(center['summary']['conversionRate'], 100)
        self.assertEqual(center['summary']['measuredImpact'], 750)
        self.assertEqual(center['summary']['unreviewed'], 0)
        self.assertIsNotNone(center['summary']['averageCycleHours'])

    def test_source_contract_uses_real_sales_rows_and_marks_aggregate_evidence(self):
        self.seed_source()
        product = dict(self.signal, entityType='product', entityId='P1')
        unknown = dict(self.signal, id='signal-2', entityType='product', entityId='UNKNOWN')
        signals = [product, unknown]
        workflow._attach_source_references(signals)
        source = product['evidence']['source']
        self.assertEqual(source['kind'], 'records')
        self.assertEqual(source['totalMatchingRows'], 1)
        self.assertEqual(source['references'][0]['sourceLine'], 7)
        self.assertEqual(source['references'][0]['invoice'], 'S-101')
        self.assertEqual(source['references'][0]['amount'], 125.5)
        self.assertNotIn('P-999', [item['invoice'] for item in source['references']])
        self.assertEqual(unknown['evidence']['source']['kind'], 'aggregate')
        self.assertEqual(unknown['evidence']['source']['references'], [])
        self.assertIn('toplu', unknown['evidence']['source']['reason'].lower())


if __name__ == '__main__':
    unittest.main()
