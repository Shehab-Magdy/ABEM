"""Normal load scenario — sustained traffic simulating production-like usage.

Run with::

    locust -f tests/load/scenarios/normal_load.py --headless \\
           -u 100 -r 10 -t 5m --host http://localhost:8000

Configuration:
    * 100 concurrent users
    * spawn rate: 10 users / second
    * duration: 5 minutes
    * wait_time: between(1, 3) (inherited from user classes)

SLA thresholds (evaluated at ``test_stop``):
    * GET endpoints P95  < 500 ms
    * POST endpoints P95 < 800 ms
    * Dashboard P95      < 1000 ms
    * Error rate         < 1 %
"""

from __future__ import annotations

import logging
from typing import Any

from dotenv import load_dotenv
from locust import between, events

from tests.load.locustfile import AdminUser, OwnerUser  # noqa: F401 — Locust discovers these

load_dotenv()

logger = logging.getLogger(__name__)

# ── Override wait_time for normal load ───────────────────────────

AdminUser.wait_time = between(1, 3)
OwnerUser.wait_time = between(1, 3)

# ── SLA configuration ───────────────────────────────────────────

_MAX_ERROR_RATE_PCT: float = 1.0
_GET_P95_MS: float = 500.0
_POST_P95_MS: float = 800.0
_DASHBOARD_P95_MS: float = 1000.0


@events.test_stop.add_listener
def _evaluate_sla(environment, **kwargs) -> None:  # type: ignore[no-untyped-def]
    """Print structured PASS / FAIL per SLA dimension after the run."""
    stats = environment.runner.stats
    total = stats.total

    total_requests = total.num_requests + total.num_failures
    error_rate = (total.num_failures / total_requests * 100) if total_requests else 0.0
    error_ok = error_rate < _MAX_ERROR_RATE_PCT

    # ── Classify endpoints ───────────────────────────────────────
    results: list[dict[str, Any]] = []

    for entry in stats.entries.values():
        name: str = entry.name
        p95 = entry.get_response_time_percentile(0.95) or 0.0

        if "dashboard" in name.lower():
            threshold = _DASHBOARD_P95_MS
            category = "DASHBOARD"
        elif entry.method == "POST":
            threshold = _POST_P95_MS
            category = "POST"
        else:
            threshold = _GET_P95_MS
            category = "GET"

        passed = p95 < threshold
        results.append({
            "name": f"{entry.method} {name}" if entry.method else name,
            "category": category,
            "p95": p95,
            "threshold": threshold,
            "passed": passed,
            "requests": entry.num_requests,
        })

    # ── Print report ─────────────────────────────────────────────
    all_passed = error_ok and all(r["passed"] for r in results)

    print("\n" + "=" * 72)
    print("  NORMAL LOAD TEST — SLA EVALUATION")
    print("=" * 72)
    print(f"  Total requests : {total_requests}")
    print(f"  Failures       : {total.num_failures}")
    print(f"  Error rate     : {error_rate:.2f}%  (limit: <{_MAX_ERROR_RATE_PCT}%)"
          f"  {'PASS' if error_ok else 'FAIL'}")
    print("-" * 72)
    print(f"  {'Endpoint':<35} {'Cat':>9} {'P95':>8} {'Limit':>8} {'Result':>7}")
    print("-" * 72)

    for r in sorted(results, key=lambda x: x["name"]):
        status = "PASS" if r["passed"] else "FAIL"
        print(
            f"  {r['name']:<35} {r['category']:>9} "
            f"{r['p95']:>7.0f}ms {r['threshold']:>7.0f}ms {status:>7}"
        )

    print("-" * 72)

    if all_passed:
        print("  OVERALL: PASS")
    else:
        print("  OVERALL: FAIL")

    print("=" * 72 + "\n")
