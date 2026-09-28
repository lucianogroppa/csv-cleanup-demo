import csv
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from clean import FIELDS, process, write_csv, CLEAN_FIELDS, REVIEW_FIELDS


class CleanupTests(unittest.TestCase):
    def test_sample_reconciles_and_quarantines_conflicts(self):
        source = Path(__file__).parent / "input" / "products.csv"
        before = source.read_bytes()
        clean, review = process(source)
        self.assertEqual((len(clean), len(review)), (4, 6))
        self.assertEqual({row["sku"] for row in clean}, {"SKU-101", "SKU-102", "SKU-106", "SKU-108"})
        self.assertEqual([row["source_row"] for row in review if row["reason"].startswith("Conflicting")], [4, 6])
        self.assertEqual(before, source.read_bytes())
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "clean.csv"
            write_csv(path, CLEAN_FIELDS, clean)
            self.assertIn("'=SUM(1+1)", path.read_text())

    def test_invalid_sibling_blocks_valid_version(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "input.csv"
            with source.open("w", newline="") as handle:
                writer = csv.writer(handle)
                writer.writerow(FIELDS)
                writer.writerow(["SKU-001", "Lamp", "Home", "10", "2"])
                writer.writerow(["sku-001", "Lamp", "Home", "bad", "2"])
            clean, review = process(source)
            self.assertEqual(clean, [])
            self.assertEqual(len(review), 2)
            self.assertTrue(all("Conflicting SKU" in row["reason"] for row in review))

    def test_wrong_shape_fails_before_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "input.csv"
            source.write_text("sku,name,category,price_usd,stock\nSKU-001,Lamp,Home,10,2,extra\n")
            with self.assertRaisesRegex(ValueError, "wrong number"):
                process(source)

    def test_cli_refuses_existing_output(self):
        root = Path(__file__).parent
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run([sys.executable, str(root / "clean.py"),
                                     str(root / "input" / "products.csv"), "--out", tmp],
                                    capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("File exists", result.stderr)


if __name__ == "__main__":
    unittest.main()
