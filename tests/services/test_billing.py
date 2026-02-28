"""Tests for billing service"""

from datetime import datetime

from src.services.billing import BillingService


class TestBilling:

    def test_fixed_price(self):
        billing = BillingService()
        start = datetime(2026, 1, 1, 10, 0)
        end = datetime(2026, 1, 1, 10, 30)
        price = billing.calculate_price(start, end, reported_degraded=False)
        assert price == 15.0

    def test_degraded_is_free(self):
        billing = BillingService()
        start = datetime(2026, 1, 1, 10, 0)
        end = datetime(2026, 1, 1, 10, 30)
        price = billing.calculate_price(start, end, reported_degraded=True)
        assert price == 0.0

    def test_payment_succeeds(self):
        billing = BillingService()
        result = billing.process_payment("tok_test", 15.0)
        assert result is True
