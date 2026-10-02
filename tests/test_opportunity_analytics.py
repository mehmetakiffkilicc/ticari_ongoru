import unittest
from analysis.opportunity_analytics import build_operations_dataset, standardize_location


def row(**changes):
    base = {'Fatura Tarihi': '2024-12-20', 'Fatura Türü': 'Satış Faturası', 'Fatura No': 'S1',
            'Malzeme Kodu': 'P1', 'Malzeme Aciklamasi': 'Ürün 1', 'Malzeme Grubu': 'Gıda',
            'Müsteri Kodu': 'C1', 'Müsteri Ünvani': 'Müşteri 1', 'Miktar': '2',
            'Net Satir Tutari': '100', 'Satir Kari': '20', 'Maliyet nach letzter EK RE': '72',
            'Sehir': '  koeln ', 'Ülke': ' DE ', 'Posta Kodu': ' 50 123 ', 'Ambar': 'Merkez', 'Satici': 'Ali'}
    base.update(changes)
    return base


class OpportunityAnalyticsTests(unittest.TestCase):
    def test_location_standardization_preserves_unknown(self):
        self.assertEqual(standardize_location(row())['city'], 'Köln')
        self.assertEqual(standardize_location(row())['postalCode'], '50123')
        self.assertFalse(standardize_location({'Sehir': '', 'Ülke': 'DE'})['complete'])

    def test_geography_excludes_purchase_and_nets_returns(self):
        rows = [row(), row(**{'Fatura No': 'R1', 'Fatura Türü': 'Satış İadesi', 'Net Satir Tutari': '25'}),
                row(**{'Fatura No': 'P1', 'Fatura Türü': 'Satın Alma Faturası', 'Net Satir Tutari': '999'})]
        result = build_operations_dataset('geography', rows, analysis_date='2024-12-30')
        self.assertEqual(result['rows'][0]['sales'], 75)
        self.assertEqual(result['kpis'][2][1], 1)

    def test_purchase_price_windows_and_stock_recommendations(self):
        rows = [
          row(**{'Fatura Tarihi':'2024-07-01','Fatura Türü':'Satın Alma Faturası','Fatura No':'A1','Miktar':'10','Net Satir Tutari':'100'}),
          row(**{'Fatura Tarihi':'2024-12-01','Fatura Türü':'Satın Alma Faturası','Fatura No':'A2','Miktar':'10','Net Satir Tutari':'120'}),
          row(**{'Fatura Tarihi':'2024-12-20','Fatura No':'S1','Miktar':'30'}),
        ]
        result = build_operations_dataset('purchasing_balance', rows, [{'code':'P1','quantity':10,'source':'demo'}], '2024-12-30')
        product = result['rows'][0]
        self.assertEqual(product['costChange'], 20)
        self.assertEqual(product['recommendation'], 'Sipariş adayı')
        self.assertTrue(result['demoStock'])

    def test_basket_metrics_have_sample_guard_and_direction(self):
        rows=[]
        for i in range(25):
            rows += [row(**{'Fatura No':f'S{i}','Müsteri Kodu':f'C{i}','Malzeme Kodu':'A','Malzeme Aciklamasi':'A'}),
                     row(**{'Fatura No':f'S{i}','Müsteri Kodu':f'C{i}','Malzeme Kodu':'B','Malzeme Aciklamasi':'B'})]
        for i in range(4):
            rows += [row(**{'Fatura No':f'X{i}','Müsteri Kodu':f'X{i}','Malzeme Kodu':'A'}),
                     row(**{'Fatura No':f'X{i}','Müsteri Kodu':f'X{i}','Malzeme Kodu':'C'})]
        result=build_operations_dataset('cross_sell',rows,analysis_date='2024-12-30')
        self.assertEqual(len(result['rows']),1)
        self.assertEqual(result['rows'][0]['confidence'],100)
        self.assertGreaterEqual(result['kpis'][3][1],1)

    def test_returns_include_effects_leaders_and_scenario(self):
        rows=[row(**{'Fatura Tarihi':'2024-12-20','Fatura Türü':'Satış İadesi','Fatura No':'R1','Net Satir Tutari':'30','Miktar':'3','Satir Kari':'6','Maliyet nach letzter EK RE':'21'}),
              row(**{'Fatura Tarihi':'2024-10-15','Fatura Türü':'Satış İadesi','Fatura No':'R2','Net Satir Tutari':'20','Miktar':'2','Satir Kari':'4','Maliyet nach letzter EK RE':'14'}),
              row(**{'Fatura Tarihi':'2024-12-10','Fatura No':'S1','Net Satir Tutari':'200'})]
        result=build_operations_dataset('returns_analysis',rows,analysis_date='2024-12-30')
        self.assertEqual(result['kpis'][0][1],50)
        self.assertEqual(result['kpis'][2][1],10)
        self.assertEqual(result['kpis'][3][1],35)
        self.assertEqual(result['scenario']['last30'],30)
        self.assertEqual(result['scenario']['next90At30DayPace'],90)
        self.assertEqual(result['products'][0]['customers'],1)
        self.assertEqual(result['customers'][0]['products'],1)


if __name__ == '__main__': unittest.main()
