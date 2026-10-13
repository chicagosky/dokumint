from django.test import TestCase

from core.utils import parse_str_to_float

class UtilTests(TestCase):
    """
    Test cases for utility functions defined in core/utils.py
    """

    def test_parse_str_to_float(self):
        _test_val = '45.67'
        self.assertEqual(parse_str_to_float(_test_val), 45.67)
        _test_val = '45'
        self.assertEqual(parse_str_to_float(_test_val), 45.0)
