from django.test import TestCase
from marketplace.services import estimate_savings

class CalculatorTests(TestCase):
    def test_calculator_savings(self):
        params = {
            'quantity': 100,
            'vehicle_rate': 10,
            'min_fare': 50,
            'selling_price': 5,
            'new_market_price': 8,
            'distance_km': 10
        }
        # Transport = max(50, 10*10) = 100
        # Mat cost = 100 * 5 = 500
        # Total = 600
        # New cost = 100 * 8 = 800
        # Savings = 200 (25%)
        result = estimate_savings(params)
        self.assertTrue(result['is_worth_it'])
        self.assertEqual(result['savings_amount'], 200)
        self.assertEqual(result['savings_percentage'], 25.0)

    def test_calculator_not_worth_it(self):
        params = {
            'quantity': 100,
            'vehicle_rate': 10,
            'min_fare': 50,
            'selling_price': 9,
            'new_market_price': 8,
            'distance_km': 10
        }
        result = estimate_savings(params)
        self.assertFalse(result['is_worth_it'])

    def test_calculator_min_fare(self):
        """Test that minimum fare is applied when distance * rate < min_fare"""
        params = {
            'quantity': 10,
            'vehicle_rate': 10,
            'min_fare': 100,
            'selling_price': 5,
            'new_market_price': 20,  # Higher new price to make it worth it
            'distance_km': 5  # 5 * 10 = 50 < 100 min fare
        }
        result = estimate_savings(params)
        self.assertEqual(result['transport_charge'], 100)  # min fare applied
        self.assertTrue(result['is_worth_it'])

    def test_calculator_zero_distance(self):
        """Test with zero distance (same location)"""
        params = {
            'quantity': 10,
            'vehicle_rate': 10,
            'min_fare': 50,
            'selling_price': 5,
            'new_market_price': 10,
            'distance_km': 0
        }
        result = estimate_savings(params)
        self.assertEqual(result['transport_charge'], 50)  # min fare applied
        self.assertEqual(result['distance_km'], 0)