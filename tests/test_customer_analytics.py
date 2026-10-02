import json
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from analysis import engine
from analysis import customer_analytics as ca


class CustomerAnalyticsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.old_root = engine.ROOT
        engine.ROOT = Path(self.temp.name)

    def tearDown(self):
        engine.ROOT = self.old_root
        self.temp.cleanup()

    def row(self, customer, day, invoice, amount, *, kind="Satış Faturası", product="P1", name=None, profit=None):
        return {
            "Fatura Türü": kind, "Fatura Tarihi": day, "Fatura No": invoice,
            "Müsteri Kodu": customer, "Müsteri Ünvani": name or f"Müşteri {customer}",
            "Sehir": "Köln", "Ülke": "DE", "Satici": "Ayşe",
            "Malzeme Kodu": product, "Malzeme Aciklamasi": f"Ürün {product}", "Malzeme Grubu": "Gıda",
            "Net Satir Tutari": str(amount), "Satir Kari": str(profit if profit is not None else amount * .2),
            "Miktar": "2", "Birim Fiyati": str(amount / 2),
        }

    def seed(self, rows):
        with closing(engine.db()) as con:
            con.execute("INSERT INTO batches(id,kind,digest,name,created,rows,accepted,rejected,snapshot,report) VALUES(?,?,?,?,?,?,?,?,?,?)",
                        ("batch","movement","digest","movement.csv","2024-12-30T12:00:00",len(rows),len(rows),0,"2024-12-30",json.dumps({})))
            for index, row in enumerate(rows, 1):
                con.execute("INSERT INTO records(batch_id,source_line,kind,fingerprint,raw,converted) VALUES(?,?,?,?,?,?)",
                            ("batch",index,"movement",f"fp-{index}",json.dumps(row),json.dumps(row)))
            con.commit()

    def test_customer_scope_excludes_purchase_and_uses_90_day_windows(self):
        self.seed([
            self.row("C1","2024-09-20","OLD",100),
            self.row("C1","2024-12-20","NEW",150),
            self.row("C1","2024-12-21","BUY",9999,kind="Satın Alma Faturası"),
            self.row("C2","2024-12-25","S2",50),
            self.row("C3","2024-12-30","S3",0),
        ])
        result = ca.customer_analytics({"analysisDate":"2024-12-30"})
        self.assertEqual(result["status"], "ready")
        customer = next(item for item in result["customers"] if item["code"] == "C1")
        self.assertEqual(customer["sales"], 150)
        self.assertEqual(customer["previousSales"], 100)
        self.assertEqual(result["periods"]["current"], ["2024-10-02", "2024-12-30"])
        self.assertEqual(result["summary"]["sales"], 200)

    def test_sale_losses_keep_their_sign_in_every_customer_view(self):
        self.seed([self.row("C1", "2024-12-20", "LOSS", 100, profit=-40)])
        overview = ca.customer_analytics({})
        self.assertEqual(overview["summary"]["profit"], -40)
        self.assertEqual(overview["customers"][0]["profit"], -40)
        detail = ca.customer_detail({"code": "C1"})
        for collection in ("timeline", "products", "invoices"):
            self.assertEqual(detail[collection][0]["profit"], -40)

    def test_lifecycle_tags_are_explainable(self):
        self.seed([
            self.row("REC","2024-01-10","R0",100), self.row("REC","2024-12-20","R1",120),
            self.row("LOST","2024-01-01","L0",200),
            self.row("NEW","2024-12-25","N1",80),
            self.row("SHRINK","2024-09-20","S0",900), self.row("SHRINK","2024-12-21","S1",10),
            self.row("GROW","2024-09-20","G0",10), self.row("GROW","2024-12-21","G1",900),
        ])
        result = ca.customer_analytics({"analysisDate":"2024-12-30"})
        by_code = {customer["code"]: customer for customer in result["customers"]}
        self.assertEqual(by_code["REC"]["segment"], "Geri kazanılan")
        self.assertTrue(any(tag["code"] == "CUSTOMER_REACTIVATED" for tag in by_code["REC"]["tags"]))
        self.assertTrue(any(tag["code"] == "CUSTOMER_LOSS_RISK" for tag in by_code["LOST"]["tags"]))
        self.assertTrue(any(tag["code"] == "CUSTOMER_NEW" for tag in by_code["NEW"]["tags"]))
        growing = next(tag for tag in by_code["GROW"]["tags"] if tag["code"] == "CUSTOMER_GROWING")
        self.assertIn("recommendedAction", growing)
        self.assertIn("scoreBreakdown", growing)
        self.assertEqual(len(growing["evidence"]["currentPeriod"]), 2)

    def test_cadence_rfm_returns_and_product_concentration(self):
        self.seed([
            self.row("C1","2024-10-10","A1",100), self.row("C1","2024-11-09","A2",100),
            self.row("C1","2024-12-09","A3",100), self.row("C1","2024-12-10","RT",50,kind="Satış İade Faturası"),
            self.row("C2","2024-12-30","MARKER",0),
        ])
        customer = ca.customer_analytics({"analysisDate":"2024-12-30"})["customers"][0]
        self.assertEqual(customer["cadence"], 30)
        self.assertEqual(customer["recency"], 21)
        self.assertEqual(customer["returns"], 50)
        self.assertEqual(len(customer["rfm"]["score"]), 3)
        self.assertTrue(any(tag["code"] == "CUSTOMER_PRODUCT_CONCENTRATION" for tag in customer["tags"]))
        self.assertTrue(any(tag["code"] == "CUSTOMER_HIGH_RETURN" for tag in customer["tags"]))

    def test_customer_detail_exposes_timeline_products_and_invoices(self):
        self.seed([
            self.row("C1","2024-11-10","A1",100,product="P1"),
            self.row("C1","2024-12-10","A2",80,product="P2"),
            self.row("C2","2024-12-11","OTHER",500,product="P9"),
        ])
        detail = ca.customer_detail({"analysisDate":"2024-12-30","code":"C1"})
        self.assertEqual(detail["status"], "ready")
        self.assertEqual([point["period"] for point in detail["timeline"]], ["2024-11","2024-12"])
        self.assertEqual({product["code"] for product in detail["products"]}, {"P1","P2"})
        self.assertEqual(len(detail["invoices"]), 2)
        self.assertEqual(ca.customer_detail({"code":"UNKNOWN"})["status"], "not_found")


if __name__ == "__main__":
    unittest.main()
