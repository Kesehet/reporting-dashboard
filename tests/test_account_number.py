import os
import sys
import unittest
from decimal import Decimal

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "api-server"))

from utils import process_account_number


class ProcessAccountNumberTests(unittest.TestCase):
    def test_decimal_account_number_is_normalized(self):
        self.assertEqual(process_account_number(Decimal("123456789")), [123456789])

    def test_decimal_with_scale_account_number_is_normalized(self):
        self.assertEqual(process_account_number(Decimal("123456789.000")), [123456789])

    def test_pipe_delimited_account_numbers_are_preserved(self):
        self.assertEqual(set(process_account_number("123|456")), {123, 456})


if __name__ == "__main__":
    unittest.main()