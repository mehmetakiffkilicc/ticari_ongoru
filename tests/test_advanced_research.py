import unittest
from datetime import date
from analysis.customer_recommendations import recommendations
from analysis.geography_locations import locate
from analysis.opportunity_analytics import build_operations_dataset

def row(code='P1',customer='C1',day='2024-12-01',category='Gıda',**extra):
    return {'Malzeme Kodu':code,'Malzeme Aciklamasi':code,'Malzeme Grubu':category,'Müsteri Kodu':customer,'Fatura Tarihi':day,'Fatura Türü':'Satış Faturası','Net Satir Tutari':100,'Satir Kari':20,**extra}

class AdvancedResearchTests(unittest.TestCase):
    def test_renewal_and_recovery_need_repeat_evidence(self):
        rows=[row(day=d) for d in ['2024-10-01','2024-11-01','2024-12-01']]+[row('OLD',day=d) for d in ['2024-01-01','2024-02-01']]+[row('ONCE',day='2024-01-01')]
        r=recommendations(rows,'C1',date(2024,12,30))['items']
        self.assertEqual({(x['code'],x['kind']) for x in r},{('P1','replenish'),('OLD','recover')})

    def test_peer_sample_and_category_rationale(self):
        rows=[row()]
        for i in range(5): rows.extend([row(customer=f'X{i}'),row('P2',customer=f'X{i}'),row('P3',customer=f'X{i}',category='İçecek')])
        items=recommendations(rows,'C1',date(2024,12,30))['items']
        self.assertEqual({(i['code'],i['kind']) for i in items},{('P2','expand'),('P3','discover')})
        self.assertEqual(recommendations(rows[:10],'C1',date(2024,12,30))['items'],[])

    def test_future_purchase_return_and_loss_candidates_are_suppressed(self):
        rows=[row()]
        for i in range(5):
            rows.extend([row(customer=f'X{i}'),row('LOSS',customer=f'X{i}',**{'Satir Kari':-20}),row('FUTURE',customer=f'X{i}',day='2025-01-01'),row('BUY',customer=f'X{i}',**{'Fatura Türü':'Satın Alma Faturası'}),row('RETURNED',customer=f'X{i}'),row('RETURNED',customer=f'X{i}',**{'Fatura Türü':'Satış İade Faturası','Net Satir Tutari':50})])
        self.assertEqual(recommendations(rows,'C1',date(2024,12,30))['items'],[])

    def test_geographic_matching_requires_country_and_preserves_unknown(self):
        self.assertEqual(locate('Almanya','Köln')['countryCode'],'DEU')
        self.assertAlmostEqual(locate('Almanya','Köln')['latitude'],50.93,delta=.2)
        self.assertIsNone(locate('Bilinmiyor','Paris')['latitude'])
        self.assertEqual(locate('TR','İstanbul')['locationStatus'],'matched')
        self.assertEqual(locate('TR','Hayalişehir')['locationStatus'],'unmatched')

    def test_geography_loss_is_not_positive_and_dates_are_scoped(self):
        result=build_operations_dataset('geography',[row(**{'Satir Kari':-20,'Sehir':'Köln','Ülke':'DE'}),row(day='2025-01-01')],analysis_date='2024-12-30')
        self.assertEqual(result['rows'][0]['profit'],-20)
        self.assertEqual(len(result['rows']),1)
        self.assertEqual(result['rows'][0]['locationStatus'],'matched')

    def test_ambiguous_city_is_not_guessed(self):
        from unittest.mock import patch
        with patch('analysis.geography_locations.city_index',return_value={'duplicate':None}):
            result=locate('DE','Duplicate')
        self.assertEqual(result['locationStatus'],'ambiguous')
        self.assertIsNone(result['latitude'])

    def test_product_history_keeps_negative_sale_margin(self):
        import tempfile,json
        from pathlib import Path
        from contextlib import closing
        from analysis import engine
        previous=engine.ROOT
        with tempfile.TemporaryDirectory() as folder:
            try:
                engine.ROOT=Path(folder)
                record=row(**{'Satir Kari':-20,'Satir Maliyeti':120,'Maliyet Fiyati':12,'Miktar':10,'Birim Fiyati':10,'Fatura No':'LOSS'})
                with closing(engine.db()) as con:
                    con.execute('INSERT INTO batches(id,kind,digest,name,created,rows,accepted,rejected,snapshot,report) VALUES(?,?,?,?,?,?,?,?,?,?)',('x','movement','x','x.csv','2024-12-01',1,1,0,None,'{}'))
                    con.execute('INSERT INTO records(batch_id,source_line,kind,fingerprint,raw,converted) VALUES(?,?,?,?,?,?)',('x',1,'movement','x',json.dumps(record),json.dumps(record)));con.commit()
                result=engine.product_detail({'code':'P1','analysisDate':'2024-12-01'})
                self.assertEqual(next(p for p in result['series'] if p['period']=='2024-12')['margin'],-20)
            finally:engine.ROOT=previous
