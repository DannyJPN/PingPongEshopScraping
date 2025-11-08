#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit test for ProductModelMemory_CS.csv extraction method

Tests extract_model() function against all entries in ProductModelMemory_CS.csv
"""

import unittest
import csv
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))
from extract_product_model import extract_model


class TestProductModelExtraction(unittest.TestCase):
    """Test model extraction against ProductModelMemory_CS.csv"""

    @classmethod
    def setUpClass(cls):
        """Load memory file once for all tests"""
        memory_file = Path(__file__).parent.parent / 'Memory' / 'ProductModelMemory_CS.csv'

        if not memory_file.exists():
            raise FileNotFoundError(f"Memory file not found: {memory_file}")

        cls.memory_data = []
        with open(memory_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, quoting=csv.QUOTE_ALL)
            for row in reader:
                cls.memory_data.append(row)

        print(f"\nLoaded {len(cls.memory_data)} entries from ProductModelMemory_CS.csv")

    def test_all_models(self):
        """Test model extraction for all entries in memory file"""
        mismatches = []
        correct = 0
        total = len(self.memory_data)

        for index, row in enumerate(self.memory_data, start=2):  # start=2 because row 1 is header
            key = row['KEY']
            expected_value = row['VALUE']

            # Extract model using our extraction method
            extracted_value = extract_model(key)

            # Compare (case-insensitive and whitespace-normalized)
            expected_normalized = ' '.join(expected_value.split()).lower()
            extracted_normalized = ' '.join(extracted_value.split()).lower()

            if extracted_normalized == expected_normalized:
                correct += 1
            else:
                mismatches.append({
                    'index': index,
                    'key': key,
                    'expected': expected_value,
                    'extracted': extracted_value
                })

        # Calculate accuracy
        accuracy = (correct / total * 100) if total > 0 else 0

        # Print results
        print(f"\n{'=' * 80}")
        print(f"MODEL EXTRACTION TEST RESULTS")
        print(f"{'=' * 80}")
        print(f"Total entries:    {total}")
        print(f"Correct matches:  {correct}")
        print(f"Mismatches:       {len(mismatches)}")
        print(f"Accuracy:         {accuracy:.2f}%")
        print(f"{'=' * 80}")

        if mismatches:
            print(f"\nAll {len(mismatches)} mismatches:")
            for i, mismatch in enumerate(mismatches, 1):
                print(f"\n{i}. Row #{mismatch['index']}: {mismatch['key']}")
                print(f"   Expected:  '{mismatch['expected']}'")
                print(f"   Extracted: '{mismatch['extracted']}'")

        # Test passes only with 100% accuracy
        self.assertEqual(accuracy, 100.0,
                        f"Model extraction accuracy {accuracy:.2f}% - must be 100%. {len(mismatches)} mismatches.")


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
