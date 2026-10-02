import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class EngineCliTests(unittest.TestCase):
    """Protect the exact module entry point used by the Next.js API route."""

    def run_engine(self, payload, data_dir):
        env = os.environ.copy()
        env["DATA_DIR"] = data_dir
        env["PYTHONIOENCODING"] = "utf-8"
        completed = subprocess.run(
            [sys.executable, "-m", "analysis.engine"],
            cwd=ROOT,
            env=env,
            input=json.dumps(payload),
            text=True,
            encoding="utf-8",
            capture_output=True,
            timeout=30,
            check=True,
        )
        return json.loads(completed.stdout)

    def test_module_entry_point_dispatches_all_specialized_analytics(self):
        actions = (
            "customer_analytics",
            "pricing_analytics",
            "seller_analytics",
            "opportunity_analytics",
        )
        with tempfile.TemporaryDirectory() as data_dir:
            for action in actions:
                with self.subTest(action=action):
                    response = self.run_engine(
                        {"action": action, "analysisDate": "2024-12-30"},
                        data_dir,
                    )
                    self.assertTrue(response["ok"], response)
                    self.assertIn("data", response)


if __name__ == "__main__":
    unittest.main()
