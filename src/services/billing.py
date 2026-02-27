from datetime import datetime


class BillingService:
    """Simple billing service for Phase 1 - fixed price"""

    FIXED_PRICE = 15.0

    def calculate_price(
        self, start_time: datetime, end_time: datetime, reported_degraded: bool
    ) -> float:
        """
        Calculate ride price.
        Phase 1: fixed 15 ILS, free if degraded reported
        """
        if reported_degraded:
            return 0.0
        return self.FIXED_PRICE

    def process_payment(self, user_payment_token: str, amount: float) -> bool:
        """Mock payment processing - always succeeds in Phase 1"""
        return True
