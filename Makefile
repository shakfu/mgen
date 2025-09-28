# Makefile for MGen development

.PHONY: help install test test-unit test-integration test-translation \
		test-py2c test-benchmark test-build clean lint format type-check \
		build docs

# Default target
help:
	@echo "MGen Development Commands"
	@echo "========================="
	@echo ""
	@echo "Setup:"
	@echo "  install       Install development dependencies"
	@echo "  install-dev   Install with all development extras"
	@echo ""
	@echo "Testing:"
	@echo "  test          Run all tests with pytest"
	@echo "  test-unit     Run unit tests only"
	@echo "  test-translation  Run translation tests only"
	@echo "  test-build    Run batch build tests (includes translation)"
	@echo "  test-integration  Run integration tests only"
	@echo "  test-py2c     Run Python-to-C conversion tests"
	@echo "  test-benchmark    Run performance benchmarks"
	@echo "  test-legacy   Display info about legacy unittest conversion"
	@echo ""
	@echo "Code Quality:"
	@echo "  lint          Run ruff linting"
	@echo "  format        Format code with ruff and isort"
	@echo "  format-check  Check code formatting without changes"
	@echo "  type-check    Run mypy type checking"
	@echo "  pre-commit    Install and run pre-commit hooks"
	@echo ""
	@echo "Build:"
	@echo "  build         Build package for distribution"
	@echo "  clean         Clean build artifacts"
	@echo ""
	@echo "Documentation:"
	@echo "  docs          Build documentation"

# Installation
install:
	uv run pip install -e .

install-dev:
	uv run pip install -e .

# Testing
test: test-pytest

test-pytest:
	uv run pytest tests/ -v --ignore=tests/test_demos.py --ignore=tests/translation

test-unit:
	uv run pytest -m "unit" tests/ -v

test-translation:
	uv run mgen batch --continue-on-error --source-dir tests/translation

test-build:
	uv run mgen batch --build --continue-on-error --source-dir tests/translation

test-integration:
	uv run pytest -m "integration" tests/ -v

test-py2c:
	uv run pytest -m "py2c" tests/ -v

test-benchmark:
	uv run pytest -m "benchmark" tests/ -v
	uv run python tests/benchmarks.py

test-coverage:
	uv run pytest --cov=src/mgen --cov-report=html --cov-report=term-missing tests/

# Code quality
lint:
	uv run ruff check src tests

format:
	uv run ruff check --fix src tests
	uv run ruff format src tests
	uv run isort --profile=black --line-length=120 src tests

format-check:
	uv run ruff check src tests
	uv run ruff format --check src tests

type-check:
	uv run mypy src/mgen

pre-commit:
	pre-commit install
	pre-commit run --all-files

# Build and distribution
build: clean
	uv build

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Documentation
docs:
	@echo "Documentation build not yet implemented"
	@echo "Planned: Sphinx documentation in doc/ directory"

# Development utilities
run-examples:
	@echo "Running example scripts..."
	uv run python examples/hello_world.py
	uv run python examples/variables.py

# CI simulation
ci-test: install-dev lint format-check type-check test

# Performance monitoring
perf-monitor:
	uv run python scripts/run_tests.py --category benchmark --verbose

# Package verification
verify-package: build
	uv run python -m twine check dist/*
	uv run pip install dist/*.whl
	uv run python -c "import mgen; print(f'MGen version: {mgen.__version__}')"

# Development server (for future web interface)
dev-server:
	@echo "Development server not yet implemented"
	@echo "Planned: Web interface for code generation and testing"