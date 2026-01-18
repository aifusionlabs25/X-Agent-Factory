# X Agent Factory Makefile
# Common development tasks

.PHONY: help test ubs install lint clean cass-index cass-search cm-build cm-client

# Default target
help:
	@echo "X Agent Factory - Available targets:"
	@echo "  make test        - Run all pytest tests"
	@echo "  make ubs         - Run UBS quality scan"
	@echo "  make ubs-info    - Run UBS scan (info only, no failure)"
	@echo "  make cass-index  - Index runs/ directory with CASS"
	@echo "  make cass-search - Search runs/ (usage: make cass-search q='query')"
	@echo "  make cm-build    - Build all memory packs"
	@echo "  make cm-client   - Build single client memory pack (usage: make cm-client slug='name')"
	@echo "  make install     - Install Python dependencies"
	@echo "  make lint        - Run basic linting"
	@echo "  make clean       - Clean generated files"

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

# CASS: Index runs/ directory
cass-index:
	@echo "🔍 Indexing runs/ with CASS..."
	@cass index runs/ --output .cass_index

# CASS: Search runs/
cass-search:
	@echo "🔍 Searching runs/ for: $(q)"
	@cass search "$(q)" --index .cass_index

# CM: Build all memory packs
cm-build:
	@echo "🧠 Building all memory packs..."
	@python tools/memory_builder.py --all

# CM: Build single client memory pack
cm-client:
	@echo "🧠 Building memory pack for: $(slug)"
	@python tools/memory_builder.py --client $(slug)

# Agent Mail: Start server (Docker)
agent-mail-up:
	@echo "📬 Starting Agent Mail server..."
	@docker run -d --name agent-mail -p 8025:8025 ghcr.io/dicklesworthstone/mcp-agent-mail || echo "Container may already be running"

# Agent Mail: Stop server
agent-mail-down:
	@echo "📬 Stopping Agent Mail server..."
	@docker stop agent-mail && docker rm agent-mail || echo "Container not running"

# Agent Mail: Health check
agent-mail-ping:
	@echo "📬 Checking Agent Mail health..."
	@python tools/agent_mail_client.py

# UMCP: Start server (Docker)
umcp-up:
	@echo "🔌 Starting UMCP Tool Bus..."
	@docker run -d --name umcp -p 8026:8026 ghcr.io/dicklesworthstone/ultimate-mcp-server || echo "Container may already be running"

# UMCP: Stop server
umcp-down:
	@echo "🔌 Stopping UMCP Tool Bus..."
	@docker stop umcp && docker rm umcp || echo "Container not running"

# UMCP: Health check
umcp-ping:
	@echo "🔌 Checking UMCP health..."
	@python tools/umcp_client.py

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
