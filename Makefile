# X Agent Factory Makefile
# Common development tasks

.PHONY: help test ubs install lint clean

# Default target
help:
	@echo "X Agent Factory - Available targets:"
	@echo "  make test      - Run all pytest tests"
	@echo "  make ubs       - Run UBS quality scan"
	@echo "  make ubs-info  - Run UBS scan (info only, no failure)"
	@echo "  make install   - Install Python dependencies"
	@echo "  make lint      - Run basic linting"
	@echo "  make clean     - Clean generated files"

# Run all tests
test:
	python -m pytest tests/ -v

# Run UBS quality gate (fails on issues)
ubs:
	@echo "🔬 Running Ultimate Bug Scanner..."
	@python tools/qa_ubs.py

# Run UBS in info mode (no failure)
ubs-info:
	@echo "🔬 Running Ultimate Bug Scanner (info mode)..."
	@python tools/qa_ubs.py --info

# Run UBS and save report
ubs-report:
	@echo "🔬 Running Ultimate Bug Scanner with report..."
	@python tools/qa_ubs.py --report

# Install dependencies
install:
	pip install -r requirements.txt
	pip install pytest jsonschema trafilatura beautifulsoup4 requests

# Basic linting
lint:
	@echo "Running basic Python syntax check..."
	python -m py_compile tools/*.py

# Clean generated files
clean:
	@echo "Cleaning generated files..."
	-rmdir /s /q __pycache__ 2>nul
	-rmdir /s /q .pytest_cache 2>nul
	-rmdir /s /q artifacts 2>nul
	@echo "Clean complete."
