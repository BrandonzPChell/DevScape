.PHONY: all lint format test coverage guardians all_tox_guardians safety_guardian coverage_guardian mypy_guardian bandit_guardian

# Default to auto-parallelization, but allow override
TOX_PARALLEL_FLAG ?= -p auto

# Run all guardians in sequence
all: guardians

help:
	@echo "Available commands:"
	@echo "  all        - Run all guardians (format, lint, test, coverage)"
	@echo "  guardians  - Run all guardians (format, lint, test, coverage)"
	@echo "  format     - Auto-format code with black and isort"
	@echo "  lint       - Run pylint"
	@echo "  test       - Run pytest"
	@echo "  coverage   - Run pytest with coverage"
	@echo "  celebrate  - Run celebrate.py"
	@echo "  all_tox_guardians - Run all configured tox environments for local checks (parallelized)"
	@echo "    (Override parallelization with: make all_tox_guardians TOX_PARALLEL_FLAG='-p 4')"
	@echo "  safety_guardian - Run only the safety dependency vulnerability scan"
	@echo "  coverage_guardian - Run only the test coverage beacon"
	@echo "  mypy_guardian - Run only the mypy type checker"
	@echo "  bandit_guardian - Run only the bandit security scanner"


guardians: format lint test coverage

# Auto-format with black and isort
format:
	tox -e lint

# Lint with pylint
lint:
	pylint src tests

# Run pytest
test:
	python -m pytest

# Run pytest with coverage
coverage:
	python -m pytest

celebrate:
	@python celebrate.py

# Run all configured tox environments for local checks (parallelized)
all_tox_guardians:
	tox $(TOX_PARALLEL_FLAG) -e lint,coverage,bandit,mypy,black,isort,safety

# Run only the safety dependency vulnerability scan
safety_guardian:
	tox -e safety

# Run only the test coverage beacon
coverage_guardian:
	tox -e coverage

# Run only the mypy type checker
mypy_guardian:
	tox -e mypy

# Run only the bandit security scanner
bandit_guardian:
	tox -e bandit

.PHONY: festival festival-win coverage clean

# POSIX (Linux/macOS/Git Bash)
festival:
	pytest -q --cov=game --cov-report=term-missing --cov-report=html | tee .coverage_summary
	@echo "Coverage summary written to .coverage_summary"
	@echo "HTML report generated at htmlcov/index.html"

# Windows PowerShell (use: make festival-win)
festival-win:
	powershell -NoProfile -Command "pytest -q --cov=game --cov-report=term-missing --cov-report=html | Tee-Object -FilePath .coverage_summary -Encoding UTF8"
	@echo Coverage summary written to .coverage_summary
	@echo HTML report generated at htmlcov/index.html



clean:
	$(RM) -r htmlcov .coverage .coverage_summary
