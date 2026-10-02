import json
import tempfile
import unittest
from contextlib import closing
from datetime import datetime
from pathlib import Path

from analysis import engine
from analysis import commercial_analytics as commercial


class CommercialAnalyticsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.old_root = engine.ROOT
        engine.ROOT = Path(self.temp.name)
        with closing(engine.db()) as con:
            con.execute("INSERT INTO batches(id,kind,digest,name,created,rows,accepted,rejected,snapshot,report) VALUES(?,?,?,?,?,?,?,?,?,?)",
                ('batch','movement','digest','movement.csv',datetime.now().isoformat(),8,8,0,'2024-12-30','{}'))
            con.commit()

    def tearDown(self):
        engine.ROOT = self.old_root
        self.temp.cleanup()

    def add(self, **changes):
        row = {'Fatura Türü':'Satış Faturası','Fatura Tarihi':'2024-12-01','Fatura No':'F1','Malzeme Grubu':'Atıştırmalık',
            'Malzeme Kodu':'P1','Malzeme Aciklamasi':'Lider ürün','Miktar':10,'Net Satir Tutari':100,
            'Satir Maliyeti':60,'Maliyet nach letzter EK RE':75,'Maliyet Fiyati':6,'Müsteri Kodu':'C1',
            'Müsteri Ünvani':'Müşteri Bir','Satici':'Ayşe','PrimVar':'×','Indirim Tutari':0}
        row.update(changes)
        with closing(engine.db()) as con:
            next_id = con.execute('SELECT COUNT(*) FROM records').fetchone()[0] + 1
            con.execute("INSERT INTO records(id,batch_id,source_line,kind,fingerprint,raw,converted) VALUES(?,?,?,?,?,?,?)",
                (next_id,'batch',next_id,'movement',f'f{next_id}','{}',json.dumps(row,ensure_ascii=False)))
            con.commit()

    def test_unit_cost_target_price_corridor_and_purchase_exclusion(self):
        self.add()
        self.add(FaturaNo='F2', **{'Fatura No':'F2','Müsteri Kodu':'C2','Müsteri Ünvani':'Müşteri İki','Net Satir Tutari':120,'Miktar':10,'Satir Maliyeti':60,'Maliyet nach letzter EK RE':80})
        self.add(**{'Fatura Türü':'Satınalma Faturası','Net Satir Tutari':9999,'Satir Maliyeti':1,'Maliyet nach letzter EK RE':1})
        result = commercial.pricing_analytics({})
        product = result['rows'][0]
        self.assertEqual(result['summary']['sales'], 220)
        self.assertAlmostEqual(product['unitPrice'], 11)
        self.assertAlmostEqual(product['recordedUnitCost'], 6)
        self.assertAlmostEqual(product['replacementUnitCost'], 7.75)
        self.assertLess(product['corridorLow'], product['corridorHigh'])
        self.assertGreater(product['targetPrice'], product['replacementUnitCost'])
        self.assertEqual(len(result['customers']), 2)

    def test_returns_reduce_sales_profit_and_replacement_cost(self):
        self.add()
        self.add(**{'Fatura Türü':'Satış İade Faturası','Fatura No':'R1','Miktar':2,'Net Satir Tutari':20,'Satir Maliyeti':12,'Maliyet nach letzter EK RE':15})
        product = commercial.pricing_analytics({})['rows'][0]
        self.assertEqual(product['sales'], 80)
        self.assertEqual(product['profit'], 32)
        self.assertEqual(product['replacementProfit'], 20)
        self.assertEqual(product['returns'], 20)

    def test_customer_price_deviation_is_explainable(self):
        self.add(**{'Müsteri Kodu':'LOW','Net Satir Tutari':50})
        self.add(**{'Fatura No':'F2','Müsteri Kodu':'HIGH','Net Satir Tutari':150})
        result = commercial.pricing_analytics({})
        deviations = {x['customerCode']: x for x in result['customers']}
        self.assertLess(deviations['LOW']['deviation'], 0)
        self.assertGreater(deviations['HIGH']['deviation'], 0)
        self.assertTrue(any(x['code']=='PRICE_CORRIDOR_WIDE' for x in result['signals']))

    def test_seller_metrics_unknown_and_coaching_signals(self):
        self.add(Satici='', **{'Maliyet nach letzter EK RE':110,'PrimVar':''})
        self.add(**{'Fatura Türü':'Satış İade Faturası','Fatura No':'R1','Net Satir Tutari':10,'Miktar':1,'Satir Maliyeti':6,'Maliyet nach letzter EK RE':11})
        result = commercial.seller_analytics({})
        unknown = next(x for x in result['rows'] if x['name']=='Bilinmiyor')
        ayse = next(x for x in result['rows'] if x['name']=='Ayşe')
        self.assertEqual(unknown['bonusCoverage'], 0)
        self.assertEqual(ayse['returns'], 10)
        self.assertTrue(any(x['code']=='SELLER_UNASSIGNED' for x in result['signals']))
        self.assertTrue(any(x['code']=='SELLER_MARGIN_COACHING' for x in result['signals']))


if __name__ == '__main__':
    unittest.main()
