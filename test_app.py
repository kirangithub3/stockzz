import unittest
from helpers import usd

class FinanceTestCase(unittest.TestCase):

    def test_usd_formatting(self):
        """Test currency formatting helper"""
        self.assertEqual(usd(1000), "$1,000.00")
        self.assertEqual(usd(2.5), "$2.50")
        self.assertEqual(usd(0), "$0.00")

    def test_app_creation(self):
        """Test that Flask app imports successfully"""
        from app import app
        self.assertIsNotNone(app)

if __name__ == '__main__':
    unittest.main()