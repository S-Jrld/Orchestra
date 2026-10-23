"""Unit tests for Budget & Cost Manager."""

import time
import unittest

from orchestra.budget.manager import BudgetExceededError, BudgetManager
from orchestra.budget.profiles import BudgetProfileManager
from orchestra.models import BudgetLimit, Tier


class TestBudget(unittest.TestCase):
    def test_tier_profiles_loaded(self):
        tiny = BudgetProfileManager.get_profile(Tier.TINY.value)
        self.assertEqual(tiny.max_calls, 3)
        self.assertLess(tiny.max_total_tokens, 5000)

        normal = BudgetProfileManager.get_profile(Tier.NORMAL.value)
        self.assertEqual(normal.max_calls, 8)

    def test_call_limit_exhaustion_raises(self):
        limit = BudgetLimit(max_calls=2, max_total_tokens=10000, max_duration_seconds=60)
        mgr = BudgetManager(limit)

        mgr.check_can_dispatch(100)
        mgr.record_usage(input_tokens=100, output_tokens=50)

        mgr.check_can_dispatch(100)
        mgr.record_usage(input_tokens=100, output_tokens=50)

        # 3rd call should trigger hard stop
        with self.assertRaises(BudgetExceededError) as ctx:
            mgr.check_can_dispatch(100)
        self.assertIn("model calls 2 >= limit 2", str(ctx.exception))

    def test_token_limit_exhaustion_raises(self):
        limit = BudgetLimit(max_calls=10, max_total_tokens=500, max_duration_seconds=60)
        mgr = BudgetManager(limit)

        # Exceed total tokens in single record
        with self.assertRaises(BudgetExceededError) as ctx:
            mgr.record_usage(input_tokens=350, output_tokens=200)
        self.assertIn("exceeded limit 500", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
