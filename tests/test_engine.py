import base64
import csv
import io
import json
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from analysis import engine as e


class IngestionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.old_root = e.ROOT
        e.ROOT = Path(self.temp.name)

    def tearDown(self):
        e.ROOT = self.old_root
        self.temp.cleanup()

    def stock(self, **changes):
        row = dict(zip(e.STOCK, ['Merkez','Çerez','0012','Ürün, özel','8','20','0,55','88','88','94,16']))
        row.update(changes)
        return row

    def movement(self, **changes):
        row = dict.fromkeys(e.MOVEMENT, '')
        row.update({'Ambar':'Merkez','Satici':'Ali','Fatura Türü':'Satış','Fatura Tarihi':'31.08.2026','Fatura No':'000123','Malzeme Grubu':'Çerez','Malzeme Kodu':'0012','Malzeme Aciklamasi':'Ürün','Birim':'PK','Miktar':'16','Birim Fiyati':'24,12','Indirim Tutari':'0','Net Satir Tutari':'385,92','Icerik':'36','Maliyet Fiyati':'0,49','Satis Fiyati':'0,67','Satir Maliyeti':'282,24','Satir Marji':'26,87','Satir Kari':'103,68','Maliyet nach letzter EK RE':'270,72','Kar nach letzter EK RE':'115,20','Marj nach letzter EK RE':'29,85','Müsteri Kodu':'00089','Müsteri Ünvani':'Örnek','Posta Kodu':'00101','Sehir':'Köln','Ülke':'DE','Sevkiyat Adresi':'Sokak, 15','Ay':'8','Yil':'2026','Cari Tipi':'1','PrimVar':'×'})
        row.update(changes)
        return row

    def inspect(self, rows, kind='stock', headers=None, encoding='utf-8-sig'):
        headers = headers or e.KINDS[kind]
        out=io.StringIO(newline='')
        writer=csv.writer(out)
        writer.writerow(headers)
        for row in rows:
            writer.writerow([row.get(h,'') for h in headers])
        return e.inspect({'kind':kind,'name':'test.csv','encoding':encoding,'file':base64.b64encode(out.getvalue().encode(encoding)).decode()})

    def analyze(self, inspected, **kwargs):
        return e.analyze({'id':inspected['id'],'mapping':inspected['mapping'],'decimal':',','dateFormat':'dmy','snapshot':'2026-08-31T18:00',**kwargs})

    def test_quotes_bom_leading_zeros_and_decimal(self):
        i=self.inspect([self.stock()]);r=self.analyze(i)
        self.assertEqual(i['preview'][0]['values'][3],'Ürün, özel')
        self.assertEqual(r['accepted'],1)
        self.assertEqual(r['preview'][0]['converted']['Kodu'],'0012')
        self.assertEqual(r['preview'][0]['converted']['Maliyet Fiyati'],'0.55')

    def test_movement_code_margin_and_raw_preservation(self):
        r=self.analyze(self.inspect([self.movement()],kind='movement'))
        v=r['preview'][0]
        self.assertEqual(v['converted']['Posta Kodu'],'00101')
        self.assertEqual(v['converted']['Satir Marji'],'0.2687')
        self.assertEqual(v['raw']['Satir Marji'],'26,87')
        self.assertEqual(r['errors'],0)

    def test_reordered_headers_match_names(self):
        i=self.inspect([self.stock()],headers=list(reversed(e.STOCK)))
        self.assertFalse(i['exactOrder'])
        self.assertEqual(self.analyze(i)['preview'][0]['converted']['Kodu'],'0012')

    def test_partial_import_and_duplicate_file(self):
        i=self.inspect([self.stock(),self.stock(Kodu='')]);r=self.analyze(i)
        self.assertEqual((r['accepted'],r['rejected']),(1,1))
        with self.assertRaises(ValueError):e.commit({'id':i['id']})
        e.commit({'id':i['id'],'acknowledge':True})
        with self.assertRaises(ValueError):e.commit({'id':i['id'],'acknowledge':True})
        self.assertEqual(e.listing()['totals']['stock'],1)
        again=self.inspect([self.stock(),self.stock(Kodu='')])
        self.assertIsNotNone(again['previous'])
        with self.assertRaises(ValueError):self.analyze(i)

    def test_blank_optional_is_not_zero(self):
        r=self.analyze(self.inspect([self.stock(**{'Maliyet Fiyati':''})]))
        self.assertIsNone(r['preview'][0]['converted']['Maliyet Fiyati'])
        self.assertEqual(r['accepted'],1)
        self.assertTrue(any(g['code']=='missing' for g in r['groups']))

    def test_invalid_numbers_dates_and_no_nan(self):
        r=self.analyze(self.inspect([self.movement(**{'Fatura Tarihi':'31.02.2026','Miktar':'NaN'})],kind='movement'))
        self.assertEqual(r['rejected'],1)
        self.assertEqual(r['errors'],2)
        self.assertEqual(str(e.number('1.234,56',',')),'1234.56')
        with self.assertRaises(ValueError):e.number('1,234.56',',')
        with self.assertRaises(ValueError):e.number('1.23,56',',')

    def test_repeated_rows_are_candidates_not_deleted(self):
        i=self.inspect([self.stock(),self.stock()]);r=self.analyze(i)
        self.assertEqual(r['accepted'],2)
        self.assertTrue(any(g['code']=='duplicate_candidate' for g in r['groups']))
        e.commit({'id':i['id'],'acknowledge':True})
        self.assertEqual(e.listing()['totals']['stock'],2)

    def test_snapshot_optional(self):
        # snapshot boş olsa bile işlem başarılı olmalı
        r = self.analyze(self.inspect([self.stock()]), snapshot='')
        self.assertEqual(r['accepted'], 1)
        self.assertTrue(bool(r['snapshot']))

    def test_encoding_windows1254(self):
        r=self.analyze(self.inspect([self.stock()],encoding='cp1254'))
        self.assertEqual(r['preview'][0]['converted']['Malzeme Grubu'],'Çerez')

    def test_missing_header_cannot_commit(self):
        i=self.inspect([self.stock()],headers=e.STOCK[:-1])
        self.assertIn(-1,i['mapping'])
        with self.assertRaises(ValueError):self.analyze(i)

    def test_broken_csv_rows_are_quarantined(self):
        text=','.join(e.STOCK)+'\nMerkez,Çerez,001,Ürün,8,20,0,55,88,88,94,16\n'
        i=e.inspect({'kind':'stock','file':base64.b64encode(text.encode()).decode()})
        r=self.analyze(i)
        self.assertEqual(r['rejected'],1)
        self.assertEqual(r['groups'][0]['code'],'column_count')

    def test_cross_file_overlap_and_export_formula_safety(self):
        row=self.stock(Aciklamasi='=HYPERLINK("example")')
        i=self.inspect([row]);self.analyze(i);e.commit({'id':i['id'],'acknowledge':True})
        newer=self.inspect([row,self.stock(Kodu='002')]);r=self.analyze(newer)
        self.assertTrue(any(g['code']=='overlap' for g in r['groups']))
        bad=self.inspect([self.stock(**{'Stok Miktari':'=1+1'})]);self.analyze(bad)
        exported=e.export_issues({'id':bad['id']})['csv']
        self.assertIn("'=1+1",exported)

    def test_semicolon_delimited_csv_and_timestamp_date(self):
        # Noktalı virgüllü stok CSV ve otomatik ayraç algılama
        text = ';'.join(e.STOCK) + '\n' + ';'.join(['Merkez','TEST-GRUP','TEST-P001','ORNEK URUN 150G','12','6','2,50','180','180','216']) + '\n'
        i = e.inspect({'kind':'stock','name':'ornek-stok.csv','encoding':'utf-8-sig','file':base64.b64encode(text.encode()).decode()})
        self.assertEqual(i['delimiter'], ';')
        r = self.analyze(i)
        self.assertEqual(r['accepted'], 1)
        self.assertEqual(r['preview'][0]['converted']['Kodu'], 'TEST-P001')
        self.assertEqual(r['preview'][0]['converted']['Maliyet Fiyati'], '2.50')

        # ERP formatında saat damgalı fatura tarihi (2023-01-02 00:00:00.000)
        mov = self.movement(**{'Fatura Tarihi': '2023-01-02 00:00:00.000'})
        out = io.StringIO(newline='')
        writer = csv.writer(out, delimiter=';')
        writer.writerow(e.MOVEMENT)
        writer.writerow([mov.get(h, '') for h in e.MOVEMENT])
        i2 = e.inspect({'kind':'movement','name':'hareket.csv','encoding':'utf-8-sig','file':base64.b64encode(out.getvalue().encode()).decode()})
        self.assertEqual(i2['delimiter'], ';')
        r2 = e.analyze({'id':i2['id'],'mapping':i2['mapping'],'decimal':',','dateFormat':'iso'})
        self.assertEqual(r2['accepted'], 1)
        self.assertEqual(r2['preview'][0]['converted']['Fatura Tarihi'], '2023-01-02')

    def test_zero_cost_is_quarantined(self):
        # Maliyeti 0 olan satır rejected (karantina) olmalı ve error üretmeli
        i = self.inspect([self.stock(**{'Maliyet Fiyati': '0'})])
        r = self.analyze(i)
        self.assertEqual(r['accepted'], 0)
        self.assertEqual(r['rejected'], 1)
        self.assertTrue(any(g['code'] == 'zero_cost' and g['severity'] == 'error' for g in r['groups']))

    def test_quality_dimensions_and_module_readiness(self):
        stock = self.inspect([self.stock()])
        self.analyze(stock)
        e.commit({'id': stock['id'], 'acknowledge': True})
        movement = self.inspect([self.movement(Satici='')], kind='movement')
        self.analyze(movement)
        e.commit({'id': movement['id'], 'acknowledge': True})
        quality = e.listing()['quality']
        self.assertEqual([d['key'] for d in quality['dimensions']], ['schema', 'completeness', 'validity', 'consistency'])
        self.assertEqual(next(d for d in quality['dimensions'] if d['key'] == 'schema')['score'], 100)
        self.assertLess(next(d for d in quality['dimensions'] if d['key'] == 'completeness')['score'], 100)
        self.assertEqual(next(m for m in quality['modules'] if m['name'] == 'Satıcı')['status'], 'partial')
        self.assertEqual(next(m for m in quality['modules'] if m['name'] == 'Satış')['status'], 'ready')
        self.assertEqual(quality['scope']['files'], 2)

    def test_quality_uses_latest_batch_per_source(self):
        first = self.inspect([self.stock(**{'Aciklamasi': ''})])
        self.analyze(first)
        e.commit({'id': first['id'], 'acknowledge': True})
        second = self.inspect([self.stock(Kodu='002')])
        self.analyze(second)
        e.commit({'id': second['id'], 'acknowledge': True})
        quality = e.listing()['quality']
        self.assertEqual(quality['scope']['files'], 1)
        self.assertEqual(next(d for d in quality['dimensions'] if d['key'] == 'completeness')['score'], 100)

    def test_product_tags_use_analysis_date_and_recalculate_replacement_values(self):
        rows = [
            self.movement(**{'Fatura Tarihi':'2024-09-20','Fatura No':'P1','Miktar':'2','Net Satir Tutari':'40','Satir Maliyeti':'20','Satir Kari':'20','Maliyet nach letzter EK RE':'24','Müsteri Kodu':'C1'}),
            self.movement(**{'Fatura Tarihi':'2024-12-20','Fatura No':'C1','Miktar':'2','Net Satir Tutari':'50','Satir Maliyeti':'30','Satir Kari':'20','Maliyet nach letzter EK RE':'40','Müsteri Kodu':'C1'}),
        ]
        movement = self.inspect(rows, kind='movement')
        self.analyze(movement)
        e.commit({'id': movement['id'], 'acknowledge': True})
        stock = self.inspect([self.stock(Kodu='0012')])
        self.analyze(stock)
        e.commit({'id': stock['id'], 'acknowledge': True})
        result = e.signals({'analysisDate':'2024-12-30'})
        product = next(p for p in result['products'] if p['code'] == '0012')
        self.assertEqual(result['analysisDate'], '2024-12-20')
        self.assertEqual(product['replacementProfit'], 10)
        self.assertEqual(product['replacementMargin'], 20)
        self.assertEqual(product['replacementCost'], 20)
        self.assertEqual(product['replacementUnitProfit'], 5)
        self.assertTrue(any(t['code'] == 'PRODUCT_REPLACEMENT_MISLEADING' for t in product['tags']))

    def test_analysis_date_simulation_does_not_create_official_run(self):
        movement = self.inspect([
            self.movement(**{'Fatura Tarihi':'2024-11-20','Fatura No':'1'}),
            self.movement(**{'Fatura Tarihi':'2024-12-20','Fatura No':'2'}),
        ], kind='movement')
        self.analyze(movement)
        e.commit({'id': movement['id'], 'acknowledge': True})
        result = e.signals({'analysisDate':'2024-12-01'})
        self.assertTrue(result['simulation'])
        with closing(e.db()) as con:
            self.assertEqual(con.execute('SELECT COUNT(*) FROM tag_runs').fetchone()[0], 0)

    def test_official_signal_is_deduplicated_and_action_is_audited(self):
        movement = self.inspect([
            self.movement(**{'Fatura Tarihi':'20.12.2024','Fatura No':'1','Net Satir Tutari':'100','Satir Maliyeti':'120','Satir Kari':'-20','Maliyet nach letzter EK RE':'125'}),
        ], kind='movement')
        self.analyze(movement); e.commit({'id':movement['id'],'acknowledge':True})
        first=e.signals({'analysisDate':'2024-12-20'})
        e.signals({'analysisDate':'2024-12-20'})
        tag=next(t for t in first['products'][0]['tags'] if t['code']=='PRODUCT_REPLACEMENT_MARGIN_RISK')
        with closing(e.db()) as con:
            self.assertEqual(con.execute('SELECT COUNT(*) FROM signal_instances WHERE id=?',(tag['signalId'],)).fetchone()[0],1)
            self.assertEqual(con.execute('SELECT COUNT(*) FROM alerts WHERE signal_id=?',(tag['signalId'],)).fetchone()[0],1)
        created=e.action_create({'signalId':tag['signalId'],'owner':'Atanmamış'})
        e.action_update({'id':created['id'],'status':'completed','outcome':'unmeasurable'})
        center=e.decision_center({})
        self.assertEqual(center['summary']['completed'],1)
        with closing(e.db()) as con:
            self.assertEqual(con.execute('SELECT COUNT(*) FROM action_events WHERE action_id=?',(created['id'],)).fetchone()[0],2)

    def test_invoice_semantics_exclude_purchase_from_sales(self):
        self.assertEqual(e.invoice_kind({'Fatura Türü':'Satın Alma Faturası'}),'purchase')
        self.assertEqual(e.invoice_kind({'Fatura Türü':'Satinalma Faturasi'}),'purchase')
        self.assertEqual(e.invoice_kind({'Fatura Türü':'Satış İade Faturası'}),'return')

    def test_role_modules_return_consistent_explainable_datasets(self):
        movement=self.inspect([
            self.movement(**{'Fatura Tarihi':'20.11.2024','Fatura No':'S1','Müsteri Ünvani':'Müşteri A','Sehir':'Berlin'}),
            self.movement(**{'Fatura Tarihi':'20.12.2024','Fatura No':'S2','Müsteri Ünvani':'Müşteri B','Sehir':'Köln'}),
            self.movement(**{'Fatura Tarihi':'21.12.2024','Fatura No':'P1','Fatura Türü':'Satın Alma Faturası'}),
        ],kind='movement')
        self.analyze(movement);e.commit({'id':movement['id'],'acknowledge':True})
        for module in ('sales_profit','returns_analysis','customers_360','salespeople','geography','pricing_costs','purchasing_balance','cross_sell','forecasting'):
            result=e.module_analytics({'module':module})
            self.assertEqual(result['status'],'ready',module)
            self.assertEqual(len(result['kpis']),4,module)
            self.assertIn('rows',result,module)
        purchasing=e.module_analytics({'module':'purchasing_balance'})
        self.assertGreater(purchasing['kpis'][0][1],0)
        sales=e.module_analytics({'module':'sales_profit'})
        self.assertLess(sales['kpis'][0][1],purchasing['kpis'][0][1]+sales['kpis'][0][1])

    def test_product_detail_aligns_returns_and_price_corridor_to_valid_scope(self):
        rows = [
            self.movement(**{'Fatura Tarihi':'01.06.2024','Fatura No':'OLD-R','Fatura Türü':'Satış İadesi','Net Satir Tutari':'99','Miktar':'1','Müsteri Kodu':'OLD','Müsteri Ünvani':'Eski Müşteri'}),
            self.movement(**{'Fatura Tarihi':'01.12.2024','Fatura No':'ZERO','Net Satir Tutari':'0','Miktar':'1'}),
        ]
        for i in range(8):
            rows.append(self.movement(**{'Fatura Tarihi':f'{10+i:02d}.12.2024','Fatura No':f'S{i}','Net Satir Tutari':str(10+i),'Miktar':'1','Müsteri Kodu':f'C{i%3}'}))
        movement = self.inspect(rows, kind='movement')
        self.analyze(movement)
        e.commit({'id': movement['id'], 'acknowledge': True})
        result = e.product_detail({'code':'0012','analysisDate':'2024-12-30'})
        self.assertEqual(result['topReturnCustomers'], [])
        self.assertTrue(result['corridor']['eligible'])
        self.assertGreater(result['corridor']['min'], 0)
        self.assertEqual(result['customers'][0]['averagePrice'], 14)

    def test_stock_analysis_models_every_product_with_stable_integer_packages(self):
        movement = self.inspect([
            self.movement(**{'Fatura Tarihi':'20.12.2024','Fatura No':'A1','Malzeme Kodu':'0012','Miktar':'9','Net Satir Tutari':'90'}),
            self.movement(**{'Fatura Tarihi':'21.12.2024','Fatura No':'B1','Malzeme Kodu':'0099','Malzeme Aciklamasi':'Stoksuz Ürün','Miktar':'6','Net Satir Tutari':'60'}),
        ], kind='movement')
        self.analyze(movement); e.commit({'id':movement['id'],'acknowledge':True})
        stock = self.inspect([self.stock(Kodu='0012', **{'Stok Miktari':'3'})])
        self.analyze(stock); e.commit({'id':stock['id'],'acknowledge':True})
        result=e.stock_analysis({'analysisDate':'2024-12-30'})
        catalogued=next(p for p in result['products'] if p['code']=='0012')
        inferred=next(p for p in result['products'] if p['code']=='0099')
        self.assertEqual(catalogued['source'],'demo')
        self.assertEqual(catalogued['content'],20)
        self.assertEqual(catalogued['contentSource'],'Stok tablosu')
        self.assertEqual(catalogued['quantity'],int(catalogued['quantity']))
        self.assertEqual(inferred['source'],'demo')
        self.assertGreater(inferred['quantity'],0)
        self.assertEqual(result['summary']['modeled'],2)
        self.assertEqual(result['summary']['contentFromStock'],1)
        repeated=e.stock_analysis({'analysisDate':'2024-12-30'})
        self.assertEqual([p['quantity'] for p in result['products']],[p['quantity'] for p in repeated['products']])


if __name__=='__main__':unittest.main()
