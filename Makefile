.PHONY: all lint format test coverage guardians

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


guardians: format lint test coverage

# Auto-format with black and isort
format:
	black .
	isort .

# Lint with pylint
lint:
	pylint game tests

# Run pytest
test:
	pytest -q

# Run pytest with coverage
coverage:
	pytest --cov=game --cov-report=term-missing

celebrate:
	@python celebrate.py

guardians: format lint test coverage

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

# Raw coverage run without tee, redirecting to file (cross-platform fallback)
coverage:
	pytest -q --cov=game --cov-report=term-missing --cov-report=html > .coverage_summary
	@type .coverage_summary 2> NUL || cat .coverage_summary
	@echo "Coverage summary written to .coverage_summary"
	@echo "HTML report generated at htmlcov/index.html"

clean:
	$(RM) -r htmlcov .coverage .coverage_summary