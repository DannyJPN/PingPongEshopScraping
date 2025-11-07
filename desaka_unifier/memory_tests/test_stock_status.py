#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit test for StockStatusMemory_CS.csv extraction method
"""

import unittest
import csv
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
from extract_stock_status import extract_stock_status


class TestStockStatusExtraction(unittest.TestCase):
    """Test stock status extraction against StockStatusMemory_CS.csv"""

    @classmethod
    def setUpClass(cls):
        """Load memory file once for all tests"""
        memory_file = Path(__file__).parent.parent / 'Memory' / 'StockStatusMemory_CS.csv'

        if not memory_file.exists():
            raise FileNotFoundError(f"Memory file not found: {memory_file}")

        cls.memory_data = []
        with open(memory_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, quoting=csv.QUOTE_ALL)
            for row in reader:
                cls.memory_data.append(row)

        print(f"\nLoaded {len(cls.memory_data)} entries from StockStatusMemory_CS.csv")

    def test_all_stock_statuses(self):
        """Test stock status extraction for all entries in memory file"""
        mismatches = []
        correct = 0
        total = len(self.memory_data)

        for row in self.memory_data:
            key = row['KEY']
            expected_value = row['VALUE']

            extracted_value = extract_stock_status(key)

            if extracted_value == expected_value:
                correct += 1
            else:
                mismatches.append({
                    'key': key,
                    'expected': expected_value,
                    'extracted': extracted_value
                })

        accuracy = (correct / total * 100) if total > 0 else 0

        print(f"\n{'=' * 80}")
        print(f"STOCK STATUS EXTRACTION TEST RESULTS")
        print(f"{'=' * 80}")
        print(f"Total entries:    {total}")
        print(f"Correct matches:  {correct}")
        print(f"Mismatches:       {len(mismatches)}")
        print(f"Accuracy:         {accuracy:.2f}%")
        print(f"{'=' * 80}")

        if mismatches:
            print(f"\nFirst 10 mismatches:")
            for i, mismatch in enumerate(mismatches[:10], 1):
                print(f"\n{i}. Key: {mismatch['key']}")
                print(f"   Expected: '{mismatch['expected']}'")
                print(f"   Extracted: '{mismatch['extracted']}'")

        self.assertGreater(accuracy, 70.0,
                          f"Stock status extraction accuracy {accuracy:.2f}% is below 70%")


if __name__ == '__main__':
    unittest.main(verbosity=2)
