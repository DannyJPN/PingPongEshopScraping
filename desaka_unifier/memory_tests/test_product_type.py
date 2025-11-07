#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit test for ProductTypeMemory_CS.csv HEURISTIC extraction method

Tests PURE HEURISTIC extract_type() function against all entries in ProductTypeMemory_CS.csv
This test does NOT use learned mappings - only pattern-based heuristics.
"""

import unittest
import csv
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))
from extract_product_type import extract_type


class TestProductTypeExtraction(unittest.TestCase):
    """Test type extraction against ProductTypeMemory_CS.csv"""

    @classmethod
    def setUpClass(cls):
        """Load memory file once for all tests"""
        memory_file = Path(__file__).parent.parent / 'Memory' / 'ProductTypeMemory_CS.csv'

        if not memory_file.exists():
            raise FileNotFoundError(f"Memory file not found: {memory_file}")

        cls.memory_data = []
        with open(memory_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, quoting=csv.QUOTE_ALL)
            for row in reader:
                cls.memory_data.append(row)

        print(f"\nLoaded {len(cls.memory_data)} entries from ProductTypeMemory_CS.csv")

    def test_all_types(self):
        """Test type extraction for all entries in memory file"""
        mismatches = []
        correct = 0
        total = len(self.memory_data)

        for index, row in enumerate(self.memory_data, start=2):  # start=2 because row 1 is header
            key = row['KEY']
            expected_value = row['VALUE']

            # Extract type using our heuristic method
            extracted_value = extract_type(key)

            # Compare (exact match)
            if extracted_value == expected_value:
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
        print(f"TYPE EXTRACTION TEST RESULTS")
        print(f"{'=' * 80}")
        print(f"Total entries:    {total}")
        print(f"Correct matches:  {correct}")
        print(f"Mismatches:       {len(mismatches)}")
        print(f"Accuracy:         {accuracy:.2f}%")
        print(f"{'=' * 80}")

        if mismatches:
            print(f"\nFirst 20 mismatches:")
            for i, mismatch in enumerate(mismatches[:20], 1):
                print(f"\n{i}. Row #{mismatch['index']}: {mismatch['key']}")
                print(f"   Expected:  '{mismatch['expected']}'")
                print(f"   Extracted: '{mismatch['extracted']}'")

        # Test passes with minimum accuracy threshold
        # For HEURISTIC (non-dictionary) type extraction, 75%+ is good
        # Type extraction is harder than brand because many products don't contain type keywords
        MIN_REQUIRED_ACCURACY = 75.0

        self.assertGreaterEqual(accuracy, MIN_REQUIRED_ACCURACY,
                        f"Type extraction accuracy {accuracy:.2f}% is below minimum {MIN_REQUIRED_ACCURACY}%. "
                        f"{len(mismatches)} mismatches found.")


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
