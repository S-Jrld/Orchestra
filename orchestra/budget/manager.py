"""Budget quota enforcement and usage tracking."""

from __future__ import annotations

import time
from typing import Dict, Optional

from orchestra.models import BudgetLimit


class BudgetExceededError(Exception):
    pass


class BudgetManager:
    """Enforces active budget limits, reserves step tokens, and halts on exhaustion."""

    def __init__(self, limits: BudgetLimit):
        self.limits = limits
        self.total_calls = 0
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.start_time = time.time()

    def get_remaining(self) -> Dict[str, Any]:
        elapsed = time.time() - self.start_time
        return {
            "calls_remaining": max(0, self.limits.max_calls - self.total_calls),
            "input_tokens_remaining": max(0, self.limits.max_input_tokens - self.total_input_tokens),
            "output_tokens_remaining": max(0, self.limits.max_output_tokens - self.total_output_tokens),
            "total_tokens_remaining": max(
                0,
                self.limits.max_total_tokens - (self.total_input_tokens + self.total_output_tokens),
            ),
            "seconds_remaining": max(0.0, self.limits.max_duration_seconds - elapsed),
        }

    def check_can_dispatch(self, estimated_tokens: int = 500) -> None:
        """Verifies if the next step can proceed under the budget."""
        elapsed = time.time() - self.start_time
        if elapsed > self.limits.max_duration_seconds:
            raise BudgetExceededError(
                f"Budget exceeded: wall-clock duration {elapsed:.1f}s > limit {self.limits.max_duration_seconds}s"
            )

        if self.total_calls >= self.limits.max_calls:
            raise BudgetExceededError(
                f"Budget exceeded: model calls {self.total_calls} >= limit {self.limits.max_calls}"
            )

        current_total = self.total_input_tokens + self.total_output_tokens
        if current_total + estimated_tokens > self.limits.max_total_tokens:
            raise BudgetExceededError(
                f"Budget exceeded: estimated tokens {current_total + estimated_tokens} > limit {self.limits.max_total_tokens}"
            )

    def record_usage(self, input_tokens: int, output_tokens: int) -> None:
        self.total_calls += 1
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens

        current_total = self.total_input_tokens + self.total_output_tokens
        if current_total > self.limits.max_total_tokens:
            raise BudgetExceededError(
                f"Budget hard stop: token consumption {current_total} exceeded limit {self.limits.max_total_tokens}"
            )
