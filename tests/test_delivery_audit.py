import unittest
from analysis.delivery_audit import error_envelope,page,reconcile


class DeliveryAuditTests(unittest.TestCase):
    def test_reconciliation_separates_sales_and_purchase(self):
        rows=[
          {'Fatura Türü':'Satış Faturası','Net Satir Tutari':'100','Satir Kari':'20'},
          {'Fatura Türü':'Satış İadesi','Net Satir Tutari':'15','Satir Kari':'3'},
          {'Fatura Türü':'Satın Alma Faturası','Net Satir Tutari':'60'},
          {'Fatura Türü':'Satın Alma İadesi','Net Satir Tutari':'5'},
        ]
        result=reconcile(rows)
        self.assertEqual(result['totals']['netSales'],85)
        self.assertEqual(result['totals']['grossProfit'],17)
        self.assertEqual(result['totals']['netPurchases'],55)
        self.assertTrue(result['passed'])

    def test_pagination_is_bounded_and_reports_next(self):
        result=page(list(range(250)),offset=100,limit=500)
        self.assertEqual(len(result['items']),100)
        self.assertEqual(result['pagination']['limit'],100)
        self.assertTrue(result['pagination']['hasNext'])
        with self.assertRaises(ValueError):page([],offset='x')

    def test_error_contract_is_stable_and_non_leaky(self):
        result=error_envelope('ANALYSIS_TIMEOUT',retryable=True,request_id='req-1')
        self.assertFalse(result['ok']);self.assertEqual(result['status'],504)
        self.assertEqual(result['error']['code'],'ANALYSIS_TIMEOUT')
        self.assertTrue(result['error']['retryable'])
        self.assertNotIn('trace',result['error'])


if __name__=='__main__':unittest.main()
