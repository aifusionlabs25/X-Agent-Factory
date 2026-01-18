"""
UBS Quality Gate Runner
Local wrapper for running Ultimate Bug Scanner on the repository.

Usage:
    python tools/qa_ubs.py          # Run scan, exit 1 on issues
    python tools/qa_ubs.py --report # Save report to artifacts/
    python tools/qa_ubs.py --info   # Info-only mode (no failure)
"""
import sys
import os
import subprocess
import argparse
from datetime import datetime
from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).parent.parent

# Directories to scan
SCAN_DIRS = [
    "tools/",
    "specialists/",
    "templates/",
    "tests/",
]


def check_ubs_installed():
    """Check if UBS is installed."""
    result = subprocess.run(
        ["ubs", "--version"],
        capture_output=True,
        text=True,
        shell=True
    )
    return result.returncode == 0


def run_ubs_scan(fail_on_warning=True, save_report=False, info_only=False):
    """Run UBS scan on the project."""
    print(f"\n{'='*60}")
    print(f"🔬 UBS QUALITY GATE")
    print(f"   Project: X Agent Factory")
    print(f"   Time: {datetime.now().isoformat()}")
    print(f"{'='*60}\n")
    
    # Check UBS installation
    if not check_ubs_installed():
        print("❌ UBS not installed.")
        print("   Install: curl -fsSL https://raw.githubusercontent.com/Dicklesworthstone/ultimate_bug_scanner/master/install.sh | bash")
        return 1
    
    # Build command
    cmd = ["ubs", "."]
    
    if fail_on_warning and not info_only:
        cmd.append("--fail-on-warning")
    
    # Add CI mode for consistent output
    cmd.append("--ci")
    
    print(f"📂 Scanning: {PROJECT_ROOT}")
    print(f"🔧 Command: {' '.join(cmd)}\n")
    
    # Run scan
    result = subprocess.run(
        cmd,
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        shell=True
    )
    
    # Print output
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    
    # Save report if requested
    if save_report:
        artifacts_dir = PROJECT_ROOT / "artifacts"
        artifacts_dir.mkdir(exist_ok=True)
        
        report_path = artifacts_dir / f"ubs-report-{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(f"UBS Scan Report - {datetime.now().isoformat()}\n")
            f.write(f"{'='*60}\n\n")
            f.write(result.stdout or "No output")
            if result.stderr:
                f.write(f"\n\nSTDERR:\n{result.stderr}")
        
        print(f"\n📄 Report saved: {report_path}")
    
    # Summary
    print(f"\n{'='*60}")
    if result.returncode == 0:
        print("✅ UBS SCAN PASSED - No critical issues found")
    else:
        print("❌ UBS SCAN FAILED - Issues found that need attention")
    print(f"{'='*60}\n")
    
    return 0 if info_only else result.returncode


def main():
    parser = argparse.ArgumentParser(description="UBS Quality Gate Runner")
    parser.add_argument("--report", action="store_true", help="Save report to artifacts/")
    parser.add_argument("--info", action="store_true", dest="info_only", help="Info mode (don't fail on issues)")
    parser.add_argument("--no-fail", action="store_true", help="Don't fail on warnings (only critical)")
    
    args = parser.parse_args()
    
    exit_code = run_ubs_scan(
        fail_on_warning=not args.no_fail,
        save_report=args.report,
        info_only=args.info_only
    )
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
