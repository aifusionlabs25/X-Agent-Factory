# Contributing to X Agent Factory

## Development Setup

1. Clone the repository:
```bash
git clone https://github.com/aifusionlabs25/X-Agent-Factory.git
cd X-Agent-Factory
```

2. Install dependencies:
```bash
pip install -r requirements.txt
make install
```

3. (Optional) Install UBS for local quality checks:
```bash
curl -fsSL "https://raw.githubusercontent.com/Dicklesworthstone/ultimate_bug_scanner/master/install.sh" | bash
```

## Quality Gates

### UBS (Ultimate Bug Scanner)

**CI Enforcement**: All PRs are scanned by UBS. PRs with critical issues cannot merge.

**Run locally before pushing:**
```bash
# Quick scan (fails on issues)
make ubs

# Info mode (no failure)
make ubs-info

# Save report to artifacts/
make ubs-report
```

Or use Python directly:
```bash
python tools/qa_ubs.py
```

### Tests

Run the test suite:
```bash
make test
# or
pytest tests/ -v
```

## Code Style

- Python: Follow PEP 8
- Use type hints where practical
- Document functions with docstrings

## Making Changes

1. Create a feature branch
2. Make your changes
3. Run `make ubs` to check for issues
4. Run `make test` to verify tests pass
5. Commit and push
6. Open a PR - CI will validate automatically
