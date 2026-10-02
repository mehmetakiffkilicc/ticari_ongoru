import unittest
from datetime import date,timedelta
from analysis.forecasting_analytics import build_forecasting_dataset,forecast_series,rolling_backtest


class ForecastingTests(unittest.TestCase):
    def test_moving_average_forecast_and_intervals(self):
        result=forecast_series([10,11,12,13]*8)
        self.assertEqual(result['status'],'ready')
        self.assertEqual(len(result['forecast']),4)
        self.assertTrue(all(x['lower']<=x['value']<=x['upper'] for x in result['forecast']))
        self.assertIsNotNone(result['mae']);self.assertIsNotNone(result['wape'])

    def test_seasonal_naive_is_evaluated_without_future_leakage(self):
        series=[10+(i%52) for i in range(80)]
        result=rolling_backtest(series)
        self.assertGreaterEqual(result['seasonal_naive_52']['points'],8)
        self.assertEqual(result['seasonal_naive_52']['mae'],0)

    def test_insufficient_history_is_explicit(self):
        result=forecast_series([0,0,2,0,1])
        self.assertEqual(result['status'],'insufficient_history')
        self.assertIn('En az',result['reason'])

    def test_candidate_requires_material_improvement(self):
        stable=forecast_series([10]*30)
        self.assertFalse(stable['candidateAccepted'])
        self.assertEqual(stable['method'],stable['baseline'])

    def test_dataset_supports_levels_pagination_and_returns(self):
        start=date(2024,1,1);rows=[]
        for week in range(30):
            day=start+timedelta(days=week*7)
            for code,qty in (('A',10),('B',5)):
                rows.append({'Fatura Tarihi':day.isoformat(),'Fatura Türü':'Satış Faturası','Fatura No':f'{code}{week}',
                  'Malzeme Kodu':code,'Malzeme Aciklamasi':f'Ürün {code}','Malzeme Grubu':'Grup','Miktar':str(qty),'Net Satir Tutari':str(qty*2)})
        rows.append({'Fatura Tarihi':(start+timedelta(days=29*7)).isoformat(),'Fatura Türü':'Satış İadesi','Fatura No':'R',
          'Malzeme Kodu':'A','Malzeme Aciklamasi':'Ürün A','Malzeme Grubu':'Grup','Miktar':'2','Net Satir Tutari':'4'})
        product=build_forecasting_dataset(rows,level='product',offset=0,limit=1)
        category=build_forecasting_dataset(rows,level='category')
        self.assertEqual(product['pagination']['total'],2);self.assertEqual(len(product['rows']),1)
        self.assertEqual(category['pagination']['total'],1)
        self.assertFalse(product['modelCard']['mlPublished'])

    def test_customer_expected_order_uses_median_cadence_and_guard(self):
        rows=[]
        for index,day in enumerate((date(2024,9,1),date(2024,10,1),date(2024,11,1),date(2024,12,1))):
            rows.append({'Fatura Tarihi':day.isoformat(),'Fatura Türü':'Satış Faturası','Fatura No':f'C{index}',
              'Müsteri Kodu':'C1','Müsteri Ünvani':'Ritimli Müşteri','Malzeme Kodu':'A','Miktar':'1','Net Satir Tutari':'10'})
        rows.append({'Fatura Tarihi':'2024-12-15','Fatura Türü':'Satış Faturası','Fatura No':'Y1',
          'Müsteri Kodu':'C2','Müsteri Ünvani':'Yeni Müşteri','Malzeme Kodu':'A','Miktar':'1','Net Satir Tutari':'10'})
        result=build_forecasting_dataset(rows,analysis_date='2025-01-10',level='customer')
        rhythm=next(x for x in result['rows'] if x['code']=='C1');new=next(x for x in result['rows'] if x['code']=='C2')
        self.assertEqual(rhythm['cadenceDays'],30)
        self.assertEqual(rhythm['expectedDate'],'2024-12-31')
        self.assertEqual(rhythm['delayDays'],10)
        self.assertEqual(new['status'],'insufficient_history')
        self.assertEqual(result['kpis'][1][1],1)


if __name__=='__main__':unittest.main()
