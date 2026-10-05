# PravahX Makefile
# Targets for setup, test, lint, run and benchmarks.
# All commands assume a Unix-like shell (WSL or Linux VM).

.PHONY: setup test lint typecheck ci run-dev validate clean help

PYTHON ?= python3
PIP ?= pip

# ── Setup ────────────────────────────────────────────────────
setup: ## Install dependencies and pre-commit hooks
	$(PIP) install -e ".[dev,backend]"
	pre-commit install

# ── Quality ──────────────────────────────────────────────────
lint: ## Run ruff linter and formatter check
	ruff check .
	ruff format --check .

typecheck: ## Run mypy strict type checking
	mypy core/pravahx backend/app

test: ## Run all tests (unit + integration, no GPU)
	pytest tests/ -m "not gpu and not e2e" --cov --cov-report=term-missing

test-unit: ## Run unit tests only
	pytest tests/unit/ --cov=core/pravahx --cov-report=term-missing

test-integration: ## Run integration tests
	pytest tests/integration/ -m "not gpu"

test-e2e: ## Run end-to-end tests
	pytest tests/e2e/

test-all: ## Run every test including GPU and e2e
	pytest tests/ --cov --cov-report=term-missing

ci: lint typecheck test ## Full CI check: lint + typecheck + test

# ── Run ──────────────────────────────────────────────────────
run-dev: ## Start all services with Docker Compose
	docker compose up -d --build

run-offline: ## Start in secure mode (no outbound network)
	docker compose -f docker-compose.yml -f docker-compose.offline.yml up -d --build

run-showcase: ## Start in showcase mode (read-only, precomputed results)
	docker compose -f docker-compose.yml -f docker-compose.showcase.yml up -d --build

stop: ## Stop all services
	docker compose down

# ── Utilities ────────────────────────────────────────────────
validate: ## Validate a scenario config: make validate CONFIG=path/to/config.yaml
	$(PYTHON) -m pravahx validate $(CONFIG)

clean: ## Remove build artefacts and caches
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	rm -rf dist/ build/ *.egg-info htmlcov/

# ── Benchmarks (later phases) ────────────────────────────────
benchmark-analytical: ## Run analytical dam break benchmark
	@echo "Benchmark runner not yet built (Phase 2+)"

benchmark-real: ## Run real dam break benchmark
	@echo "Benchmark runner not yet built (Phase 12)"

# ── Help ─────────────────────────────────────────────────────
help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help
