#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit test for CategoryMemory_CS.csv extraction method
"""

import unittest
import csv
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
from extract_category import extract_category


class TestCategoryExtraction(unittest.TestCase):
    """Test category extraction against CategoryMemory_CS.csv"""

    @classmethod
    def setUpClass(cls):
        """Load memory file once for all tests"""
        memory_file = Path(__file__).parent.parent / 'Memory' / 'CategoryMemory_CS.csv'

        if not memory_file.exists():
            raise FileNotFoundError(f"Memory file not found: {memory_file}")

        cls.memory_data = []
        with open(memory_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, quoting=csv.QUOTE_ALL)
            for row in reader:
                cls.memory_data.append(row)

        print(f"\nLoaded {len(cls.memory_data)} entries from CategoryMemory_CS.csv")

    def test_all_categories(self):
        """Test category extraction for all entries in memory file"""
        mismatches = []
        correct = 0
        total = len(self.memory_data)

        for row in self.memory_data:
            key = row['KEY']
            expected_value = row['VALUE']

            extracted_value = extract_category(key)

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
        print(f"CATEGORY EXTRACTION TEST RESULTS")
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

        self.assertGreater(accuracy, 60.0,
                          f"Category extraction accuracy {accuracy:.2f}% is below 60%")


if __name__ == '__main__':
    unittest.main(verbosity=2)
