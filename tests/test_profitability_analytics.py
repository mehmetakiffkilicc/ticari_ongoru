import json
import tempfile
import unittest
from contextlib import closing
from datetime import datetime
from pathlib import Path

from analysis import engine
from analysis import profitability_analytics as profit


class ProfitabilityAnalyticsTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.old_root=engine.ROOT;engine.ROOT=Path(self.temp.name)
        with closing(engine.db()) as con:
            con.execute("INSERT INTO batches(id,kind,digest,name,created,rows,accepted,rejected,snapshot,report) VALUES(?,?,?,?,?,?,?,?,?,?)",('b','movement','d','m.csv',datetime.now().isoformat(),10,10,0,'2024-12-30','{}'));con.commit()

    def tearDown(self):engine.ROOT=self.old_root;self.temp.cleanup()

    def add(self,**changes):
        row={'Fatura Türü':'Satış Faturası','Fatura Tarihi':'2024-12-01','Fatura No':'F1','Malzeme Grubu':'G1','Malzeme Kodu':'P1','Müsteri Kodu':'C1','Müsteri Ünvani':'Müşteri 1','Satici':'Ali','Ambar':'Merkez','Miktar':10,'Net Satir Tutari':100,'Indirim Tutari':10,'Satir Maliyeti':60,'Maliyet nach letzter EK RE':75}
        row.update(changes)
        with closing(engine.db()) as con:
            i=con.execute('SELECT COUNT(*) FROM records').fetchone()[0]+1
            con.execute("INSERT INTO records(id,batch_id,source_line,kind,fingerprint,raw,converted) VALUES(?,?,?,?,?,?,?)",(i,'b',i,'movement',f'f{i}','{}',json.dumps(row,ensure_ascii=False)));con.commit()

    def test_waterfall_reconciles_and_purchase_is_excluded(self):
        self.add();self.add(**{'Fatura Türü':'Satış İade Faturası','Fatura No':'R1','Net Satir Tutari':20,'Indirim Tutari':0,'Miktar':2,'Satir Maliyeti':12,'Maliyet nach letzter EK RE':15});self.add(**{'Fatura Türü':'Satınalma Faturası','Net Satir Tutari':9999})
        out=profit.sales_profitability({});m=out['metrics'];wf={x['key']:x['value'] for x in out['waterfall']}
        self.assertEqual((m['grossSales'],m['discounts'],m['returns'],m['netSales']),(110,10,20,80))
        self.assertEqual((m['cogs'],m['grossProfit'],m['replacementProfit']),(48,32,20))
        self.assertEqual(wf['gross']+wf['discount']+wf['returns'],wf['net'])
        self.assertEqual(wf['net']+wf['cogs'],wf['profit'])

    def test_granularity_changes_below_ninety_days(self):
        self.add(**{'Fatura Tarihi':'2024-01-01'});self.add(**{'Fatura Tarihi':'2024-12-01','Fatura No':'F2'})
        self.assertEqual(profit.sales_profitability({})['granularity'],'month')
        scoped=profit.sales_profitability({'start':'2024-11-01','end':'2024-12-30'})
        self.assertEqual(scoped['granularity'],'day')

    def test_breakdowns_share_same_economics(self):
        self.add();self.add(**{'Fatura No':'F2','Müsteri Kodu':'C2','Müsteri Ünvani':'Müşteri 2','Satici':'Ayşe','Ambar':'Batı','Malzeme Grubu':'G2','Net Satir Tutari':200,'Satir Maliyeti':100,'Maliyet nach letzter EK RE':120})
        out=profit.sales_profitability({})
        for key in ('category','customer','seller','warehouse'):
            self.assertAlmostEqual(sum(x['netSales'] for x in out['breakdowns'][key]),out['metrics']['netSales'])
        self.assertEqual(len(out['breakdowns']['customer']),2)

    def test_executive_snapshot_includes_open_action(self):
        self.add(**{'Maliyet nach letzter EK RE':110})
        with closing(engine.db()) as con:
            now=datetime.now().isoformat();con.execute("INSERT INTO actions(id,alert_id,signal_id,entity_type,entity_id,title,description,priority,status,owner,due_date,outcome,realized_impact,created,updated) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",('a1',None,None,'product','P1','Fiyatı incele','', 'high','open','Yönetici','2024-12-31',None,None,now,now));con.commit()
        snap=profit.executive_snapshot({})
        self.assertTrue(any(x['type']=='action' and x['entityId']=='a1' for x in snap['items']))
        self.assertTrue(any(x['type']=='risk' for x in snap['items']))


if __name__=='__main__':unittest.main()
