import copy
import json
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

from analysis import engine
from analysis import decision_cases as cases


class DecisionCaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.old = engine.ROOT
        engine.ROOT = Path(self.temp.name)
        cases.seed({'scope': 'demo'})

    def tearDown(self):
        engine.ROOT = self.old
        self.temp.cleanup()

    def get(self, identifier='demo-stock-pending'):
        return cases.detail({'scope':'demo','id':identifier})

    def act(self, doc, operation, **kwargs):
        return cases.mutate({'scope':doc['scope'],'id':doc['id'],'version':doc['version'],'operation':operation,**kwargs})

    def dump(self):
        with closing(engine.db()) as con:
            return list(con.iterdump())

    def test_nine_fixtures_are_separate_idempotent_and_reads_do_not_change_them(self):
        initial = self.dump()
        for _ in range(3):
            self.assertEqual(len(cases.listing({'scope':'demo'})['cases']), 9)
            self.assertEqual(cases.listing({'scope':'live'})['cases'], [])
            self.get()
        self.assertEqual(initial, self.dump())
        cases.seed({'scope':'demo'})
        self.assertEqual(initial, self.dump())
        for category, days in [('stock',7),('pricing',30),('customer',14)]:
            doc = self.get(f'demo-{category}-pending')
            self.assertEqual(doc['proposal']['followupDays'],days)
            self.assertFalse(doc['overdue'])

    def test_start_without_approval_and_apply_without_start_fail_atomically(self):
        doc = self.get()
        initial = self.dump()
        for operation in ('start','apply','feedback'):
            with self.assertRaises(ValueError):self.act(doc,operation)
        self.assertEqual(initial,self.dump())
        approved=self.act(doc,'approve')
        with self.assertRaises(ValueError):self.act(approved,'apply',note='Uygulama denemesi')
        self.assertEqual(self.get()['state'],'approved')

    def test_duplicate_and_concurrent_approval_create_one_task(self):
        doc=self.get()
        def approve():
            try:return self.act(doc,'approve')['state']
            except ValueError:return 'stale'
        with ThreadPoolExecutor(max_workers=2) as pool:
            results=list(pool.map(lambda _:approve(),range(2)))
        self.assertEqual(sorted(results),['approved','stale'])
        self.assertEqual(len(self.get()['tasks']),1)
        self.assertEqual(len(self.get()['approvals']),1)

    def test_changed_scope_supersedes_task_and_needs_new_approval(self):
        doc=self.act(self.get(),'approve')
        snapshot=copy.deepcopy(doc['snapshot'])
        proposal={**doc['proposal'],'owner':'Yeni sorumlu'}
        doc=self.act(doc,'edit',proposal=proposal)
        self.assertEqual(doc['state'],'pending')
        self.assertEqual(doc['revision'],2)
        self.assertIsNone(doc['task'])
        self.assertEqual(doc['tasks'][0]['status'],'superseded')
        self.assertEqual(doc['approvals'][0]['revision'],1)
        with self.assertRaises(ValueError):self.act(doc,'start')
        doc=self.act(doc,'approve')
        self.assertEqual(doc['task']['owner'],'Yeni sorumlu')
        self.assertEqual(doc['snapshot'],snapshot)

    def test_application_sets_followup_without_claiming_success(self):
        doc=self.act(self.act(self.get(),'approve'),'start')
        initial=self.dump()
        with self.assertRaises(ValueError):self.act(doc,'apply',note='')
        self.assertEqual(initial,self.dump())
        doc=self.act(doc,'apply',note='Alım görevi tamamlandı.')
        self.assertEqual(doc['state'],'monitoring')
        self.assertEqual(doc['task']['followupDate'],'2025-01-06')
        self.assertIsNone(doc['feedback'])
        self.assertFalse(doc['followupReady'])
        with self.assertRaises(ValueError):self.act(doc,'feedback',outcome='met',before=8,after=30,note='Yeterli takip verisi',unit='gün',evidence='Sayım raporu')
        with self.assertRaises(ValueError):self.act(doc,'edit',proposal=doc['proposal'])

    def test_feedback_requires_due_date_values_evidence_and_keeps_zero(self):
        doc=self.get('demo-stock-monitoring')
        self.assertTrue(doc['followupReady'])
        for changes in ({'after':None},{'after':float('nan')},{'evidence':''}):
            payload={'outcome':'not_met','before':8,'after':0,'unit':'gün','evidence':'Fiziksel sayım','note':'Ürün stokta kalmadı.',**changes}
            with self.assertRaises(ValueError):self.act(doc,'feedback',**payload)
        doc=self.act(doc,'feedback',outcome='not_met',before=8,after=0,unit='gün',evidence='Fiziksel sayım',note='Ürün stokta kalmadı.')
        self.assertEqual(doc['feedback']['after'],0)
        self.assertEqual(doc['feedback']['source'],'user_reported')
        self.assertEqual(doc['state'],'reviewed')

    def test_missing_data_is_unmeasurable_not_success(self):
        doc=self.act(self.get('demo-stock-monitoring'),'feedback',outcome='unmeasurable',note='Yeni sayım verisi alınamadı.')
        self.assertIsNone(doc['feedback']['before'])
        self.assertIsNone(doc['feedback']['after'])
        self.assertEqual(doc['feedback']['outcome'],'unmeasurable')

    def test_rejection_requires_reason_and_reopen_preserves_history(self):
        doc=self.get()
        with self.assertRaises(ValueError):self.act(doc,'reject',note='yok')
        rejected=self.act(doc,'reject',note='Mevcut tedarik anlaşması kontrol edilmeli.')
        child=self.act(rejected,'reopen')
        self.assertEqual(child['parentId'],rejected['id'])
        self.assertEqual(child['state'],'pending')
        self.assertEqual(child['clockDate'],cases.DEMO_DATE)
        self.assertEqual(self.get()['state'],'rejected')
        self.assertEqual(self.act(self.get(),'reopen')['id'],child['id'])

    def test_scope_is_enforced_and_demo_reset_preserves_legacy_and_live(self):
        doc=self.get()
        with self.assertRaises(ValueError):cases.mutate({'scope':'live','id':doc['id'],'version':doc['version'],'operation':'approve'})
        with self.assertRaises(ValueError):cases.seed({'scope':'live','reset':True})
        with closing(engine.db()) as con:
            con.execute("INSERT INTO batches VALUES('B','stock','digest','source.csv','2024-12-30',0,0,0,'2024-12-30','{}')")
            con.execute("""INSERT INTO actions(id,entity_type,entity_id,title,description,priority,status,owner,created,updated)
                        VALUES('legacy-1','product','P1','Eski aksiyon','Mevcut kayıt','high','open','Yönetici','2024-12-20','2024-12-20')""")
            live=copy.deepcopy(doc);live['id']='live-kept';live['scope']='live';live['origin']='live-kept'
            cases._insert(con,live)
            con.commit()
        cases.seed({'scope':'demo','reset':True})
        self.assertEqual(len(cases.listing({'scope':'live'})['cases']),1)
        self.assertEqual(cases.listing({'scope':'live'})['legacy'][0]['id'],'legacy-1')
        with closing(engine.db()) as con:self.assertEqual(con.execute('SELECT COUNT(*) FROM batches').fetchone()[0],1)

    def test_evaluation_is_explicit_deduplicated_and_freezes_evidence(self):
        signal={'id':'S1','module':'pricing','entityId':'P1','entityName':'Ürün','title':'Marj düşüşü','code':'MARGIN',
                'score':80,'confidence':'Orta','evidence':{'observed':12,'threshold':22},'recommendedAction':'Fiyatı inceleyin.'}
        with patch('analysis.decision_workflow._collect',return_value=('2024-12-30',[signal])),patch.object(engine,'stock_analysis',return_value={'products':[]}):
            first=cases.evaluate({'scope':'live'})
            second=cases.evaluate({'scope':'live'})
        self.assertEqual(len(second['cases']),1)
        self.assertEqual(first['cases'][0]['snapshot']['observed'],12)
        signal['evidence']['observed']=99
        self.assertEqual(cases.listing({'scope':'live'})['cases'][0]['snapshot']['observed'],12)

    def test_api_reads_do_not_generate_tag_runs_or_unified_occurrences(self):
        from analysis import decision_workflow
        initial=self.dump()
        with patch.object(decision_workflow,'synchronize',side_effect=AssertionError('Read evaluated signals')):
            engine.main({'action':'unified_decision_center'})
        # Compatibility endpoint may initialize its schema once, but repeated
        # reads must not add signal runs, occurrences or action events.
        after_schema=self.dump()
        engine.main({'action':'unified_decision_center'})
        self.assertEqual(after_schema,self.dump())
        with patch.object(engine,'signals',return_value={}) as collect:
            engine.main({'action':'signals'})
            self.assertFalse(collect.call_args.args[0]['persist'])

    def test_future_source_rows_are_not_cited_in_historic_decisions(self):
        from analysis import decision_workflow
        with closing(engine.db()) as con:
            con.execute("INSERT INTO batches VALUES('B','movement','digest','source.csv','2024-12-30',1,1,0,'2024-12-30','{}')")
            row={'Fatura Türü':'Satış','Malzeme Kodu':'P1','Fatura Tarihi':'2024-12-25','Net Satir Tutari':'10'}
            con.execute("INSERT INTO records(batch_id,source_line,kind,fingerprint,raw,converted) VALUES('B',9,'movement','F','{}',?)",(json.dumps(row),))
            con.commit()
        signal={'entityType':'product','entityId':'P1','evidence':{}}
        decision_workflow._attach_source_references([signal],'2024-12-20')
        self.assertEqual(signal['evidence']['source']['references'],[])

    def test_commercial_scope_honors_analysis_date_including_same_day_timestamps(self):
        from analysis.commercial_analytics import _scope
        rows=[{'Fatura Türü':'Satış','Fatura Tarihi':day} for day in ['2024-12-19','2024-12-20T13:00:00','2024-12-21']]
        self.assertEqual(len(_scope(rows,{'analysisDate':'2024-12-20'})),2)
        self.assertEqual(len(_scope(rows,{'start':'2024-12-20','end':'2024-12-20'})),1)

    def test_profile_proposal_is_verified_deduplicated_and_requires_approval(self):
        dataset={'analysisDate':'2024-12-20','periods':{'current':['2024-09-22','2024-12-20']},
                 'products':[{'code':'P1','name':'Kaynak Ürün','sales':100,'profit':20,'tags':[]}]}
        payload={'scope':'live','entityType':'product','code':'P1','analysisDate':'2024-12-30',
                 'description':'Müşteri grubuna göre fiyatları inceleyin.','successMetric':'Marjı %22 hedefine çıkarın.'}
        with patch.object(engine,'signals',return_value=dataset):
            doc=cases.from_entity(payload)
            again=cases.from_entity(payload)
            self.assertEqual(doc['id'],again['id'])
            self.assertEqual(doc['snapshot']['analysisDate'],'2024-12-20')
            self.assertEqual(doc['snapshot']['entityType'],'product')
            self.assertEqual(doc['snapshot']['observed'],100)
            self.assertEqual(doc['state'],'pending')
            self.assertEqual(doc['approvals'],[])
            self.assertEqual(doc['proposal']['successMetric'],payload['successMetric'])
            with self.assertRaises(ValueError):self.act(doc,'start')
            with self.assertRaises(ValueError):cases.from_entity({**payload,'code':'UNKNOWN'})
            with self.assertRaises(ValueError):cases.from_entity({**payload,'scope':'demo'})
            with self.assertRaises(ValueError):cases.from_entity({**payload,'successMetric':''})

    def test_customer_profile_proposal_preserves_entity_identity(self):
        dataset={'analysisDate':'2024-12-30','periods':{'current':['2024-10-02','2024-12-30']},
                 'customers':[{'code':'C1','name':'Kaynak Müşteri','sales':200,'profit':40,'tags':[]}]}
        with patch('analysis.customer_analytics.customer_analytics',return_value=dataset):
            doc=cases.from_entity({'scope':'live','entityType':'customer','code':'C1','analysisDate':'2024-12-30',
                                  'description':'Yeni ürün teklifi hazırlayın.','successMetric':'İki ürünlük deneme siparişi alın.'})
        self.assertEqual(doc['category'],'customer')
        self.assertEqual(doc['snapshot']['entityId'],'C1')
        self.assertEqual(doc['proposal']['followupDays'],14)


if __name__=='__main__':unittest.main()
