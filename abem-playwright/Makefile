# ABEM Playwright & Locust — Test Run Targets

.PHONY: install test-auth test-expenses test-payments test-dashboards \
        test-financial test-rbac test-ui-all test-ui-parallel \
        load-smoke load-normal load-stress load-interactive test-all

install:
	pip install -r requirements.txt
	playwright install chromium

# ── UI Tests ──────────────────────────────────────────────

test-auth:
	pytest tests/ui/auth/ -v -m "sprint1 or auth"

test-expenses:
	pytest tests/ui/expenses/ -v -m "sprint3 or expenses"

test-payments:
	pytest tests/ui/payments/ -v -m "sprint4 or payments"

test-dashboards:
	pytest tests/ui/dashboard/ -v -m "sprint5 or dashboard"

test-financial:
	pytest tests/ui/ -v -m financial

test-rbac:
	pytest tests/ui/ -v -m rbac

test-ui-all:
	pytest tests/ui/ -v --html=reports/ui_report.html --self-contained-html

test-ui-parallel:
	pytest tests/ui/ -v -n auto --html=reports/ui_report.html --self-contained-html

# ── Load Tests ────────────────────────────────────────────

load-smoke:
	cd tests/load && locust -f scenarios/smoke_load.py --headless -u 10 -r 2 --run-time 30s

load-normal:
	cd tests/load && locust -f scenarios/normal_load.py --headless -u 100 -r 10 --run-time 5m \
		--html reports/normal_load.html --csv reports/normal

load-stress:
	cd tests/load && locust -f scenarios/stress_test.py --headless \
		--html reports/stress_test.html --csv reports/stress

load-interactive:
	cd tests/load && locust -f locustfile.py

# ── Full regression ───────────────────────────────────────

test-all:
	pytest tests/ui/ -v -n auto --html=reports/regression_report.html --self-contained-html
	cd tests/load && locust -f scenarios/smoke_load.py --headless -u 10 -r 2 --run-time 30s
