"""Smoke load scenario — quick validation that the API handles light traffic.

Run with::

    locust -f tests/load/scenarios/smoke_load.py --headless \\
           -u 10 -r 2 -t 30s --host http://localhost:8000

Configuration:
    * 10 concurrent users
    * spawn rate: 2 users / second
    * duration: 30 seconds
    * wait_time: between(1, 3) (inherited from user classes)

Pass criteria (evaluated at ``test_stop``):
    * Error rate < 1 %
    * P95 response time < 500 ms
"""

from __future__ import annotations

import logging

from dotenv import load_dotenv
from locust import between, events

from tests.load.locustfile import AdminUser, OwnerUser  # noqa: F401 — Locust discovers these

load_dotenv()

logger = logging.getLogger(__name__)

# ── Override wait_time for smoke scenario ────────────────────────

AdminUser.wait_time = between(1, 3)
OwnerUser.wait_time = between(1, 3)

# ── SLA evaluation at test stop ─────────────────────────────────

_MAX_ERROR_RATE_PCT: float = 1.0
_MAX_P95_MS: float = 500.0


@events.test_stop.add_listener
def _evaluate_sla(environment, **kwargs) -> None:  # type: ignore[no-untyped-def]
    """Print a structured PASS / FAIL verdict after the test run."""
    stats = environment.runner.stats
    total = stats.total

    total_requests = total.num_requests + total.num_failures
    error_rate = (total.num_failures / total_requests * 100) if total_requests else 0.0
    p95 = total.get_response_time_percentile(0.95) or 0.0

    error_ok = error_rate < _MAX_ERROR_RATE_PCT
    p95_ok = p95 < _MAX_P95_MS

    print("\n" + "=" * 60)
    print("  SMOKE LOAD TEST — SLA EVALUATION")
    print("=" * 60)
    print(f"  Total requests : {total_requests}")
    print(f"  Failures       : {total.num_failures}")
    print(f"  Error rate     : {error_rate:.2f}%  (limit: <{_MAX_ERROR_RATE_PCT}%)"
          f"  {'PASS' if error_ok else 'FAIL'}")
    print(f"  P95 latency    : {p95:.0f} ms  (limit: <{_MAX_P95_MS:.0f} ms)"
          f"  {'PASS' if p95_ok else 'FAIL'}")
    print("-" * 60)

    if error_ok and p95_ok:
        print("  OVERALL: PASS")
    else:
        print("  OVERALL: FAIL")

    print("=" * 60 + "\n")
