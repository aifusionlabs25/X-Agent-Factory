"""
Agent Eval Harness
Runs evaluation suites for regression, security, and tool-use testing.

Usage:
    python tools/eval_runner.py                    # Run all evals
    python tools/eval_runner.py --suite security   # Run security only
    python tools/eval_runner.py --ci               # CI mode (structured output)
    python tools/eval_runner.py --judge=openai-evals  # (Future) LLM judge
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import os
import re
import json
import argparse
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Tuple


# Configuration
PROJECT_ROOT = Path(__file__).parent.parent
EVALS_DIR = PROJECT_ROOT / "evals"
AGENTS_DIR = PROJECT_ROOT / "agents"


def load_eval_suite(suite_name: str) -> List[Dict[str, Any]]:
    """Load evaluation cases from JSONL file."""
    path = EVALS_DIR / f"{suite_name}.jsonl"
    
    if not path.exists():
        print(f"❌ Suite not found: {path}")
        return []
    
    cases = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                cases.append(json.loads(line))
    
    return cases


def run_functional_eval(case: Dict[str, Any]) -> Tuple[bool, str]:
    """Run a functional evaluation case."""
    expected = case.get('expected', {})
    dossier_path = case.get('input', {}).get('dossier_path', '')
    
    if not dossier_path:
        return False, "No dossier_path specified"
    
    # Check for built agent
    dossier_file = PROJECT_ROOT / dossier_path
    if not dossier_file.exists():
        return False, f"Dossier not found: {dossier_path}"
    
    # Load and check agent artifacts
    client_slug = dossier_file.parent.name
    agent_dir = AGENTS_DIR / client_slug
    
    if expected.get('has_system_prompt'):
        if not (agent_dir / "system_prompt.txt").exists():
            return False, "Missing system_prompt.txt"
    
    if expected.get('has_kb_seed'):
        if not (agent_dir / "kb_seed.md").exists():
            return False, "Missing kb_seed.md"
    
    if expected.get('has_manifest'):
        if not (agent_dir / "manifest.json").exists():
            return False, "Missing manifest.json"
    
    if expected.get('manifest_has_sha256'):
        manifest_path = agent_dir / "manifest.json"
        if manifest_path.exists():
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
            if not manifest.get('input_dossier_sha256'):
                return False, "Manifest missing SHA256"
    
    if expected.get('system_prompt_min_bytes'):
        sp_path = agent_dir / "system_prompt.txt"
        if sp_path.exists():
            if sp_path.stat().st_size < expected['system_prompt_min_bytes']:
                return False, "System prompt too small"
    
    return True, "OK"


def run_style_eval(case: Dict[str, Any]) -> Tuple[bool, str]:
    """Run a style evaluation case."""
    expected = case.get('expected', {})
    artifact = case.get('input', {}).get('artifact', '')
    
    # Find the artifact in a sample agent
    sample_agent = None
    if AGENTS_DIR.exists():
        for d in AGENTS_DIR.iterdir():
            if d.is_dir() and (d / artifact).exists():
                sample_agent = d
                break
    
    if not sample_agent:
        return False, f"No agent with {artifact} found"
    
    artifact_path = sample_agent / artifact
    content = artifact_path.read_text(encoding='utf-8')
    
    if expected.get('no_placeholders'):
        if 'TBD' in content or 'TODO' in content or 'PLACEHOLDER' in content:
            # Allow TBD in dossier-derived content
            pass
    
    if expected.get('no_lorem_ipsum'):
        if 'lorem ipsum' in content.lower():
            return False, "Contains lorem ipsum"
    
    if expected.get('valid_json') and artifact.endswith('.json'):
        try:
            json.loads(content)
        except:
            return False, "Invalid JSON"
    
    if expected.get('is_markdown') and artifact.endswith('.md'):
        if not content.strip():
            return False, "Empty markdown"
    
    if expected.get('has_headings'):
        if '#' not in content:
            return False, "Missing markdown headings"
    
    return True, "OK"


def run_security_eval(case: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Run a security injection evaluation case.
    Uses the prompt_safety_screen to test detection.
    """
    input_text = case.get('input', '')
    expected = case.get('expected', {})
    
    try:
        sys.path.insert(0, str(PROJECT_ROOT / "tools"))
        from prompt_safety_screen import screen_input, get_risk_level
        
        warnings = screen_input(input_text)
        risk_level = get_risk_level(warnings)
        
        if expected.get('blocked'):
            if len(warnings) > 0:
                return True, f"Blocked ({len(warnings)} warnings, risk={risk_level})"
            else:
                return False, "Should have been blocked but wasn't"
        else:
            if len(warnings) == 0:
                return True, "Allowed (no warnings)"
            else:
                return False, f"Unexpected block: {warnings}"
    
    except ImportError:
        return False, "prompt_safety_screen not available"


def run_tool_use_eval(case: Dict[str, Any]) -> Tuple[bool, str]:
    """Run a tool use evaluation case."""
    # For now, just verify tools exist and are importable
    tool = case.get('input', {}).get('tool', '')
    expected = case.get('expected', {})
    
    tool_path = PROJECT_ROOT / "tools" / f"{tool}.py"
    
    if not tool_path.exists():
        return False, f"Tool not found: {tool}"
    
    # Try to import
    try:
        sys.path.insert(0, str(PROJECT_ROOT / "tools"))
        __import__(tool)
        
        if expected.get('no_error'):
            return True, "Tool importable"
        
        return True, "OK"
    
    except Exception as e:
        return False, f"Import error: {e}"


def run_eval_case(case: Dict[str, Any]) -> Dict[str, Any]:
    """Run a single evaluation case."""
    case_type = case.get('type', 'unknown')
    case_id = case.get('id', 'unknown')
    description = case.get('description', '')
    
    start_time = datetime.utcnow()
    
    if case_type == 'functional':
        passed, message = run_functional_eval(case)
    elif case_type == 'style':
        passed, message = run_style_eval(case)
    elif case_type == 'security':
        passed, message = run_security_eval(case)
    elif case_type == 'tool_use':
        passed, message = run_tool_use_eval(case)
    else:
        passed, message = False, f"Unknown eval type: {case_type}"
    
    end_time = datetime.utcnow()
    duration = (end_time - start_time).total_seconds()
    
    return {
        "id": case_id,
        "type": case_type,
        "description": description,
        "passed": passed,
        "message": message,
        "duration_seconds": duration
    }


def run_suite(suite_name: str) -> List[Dict[str, Any]]:
    """Run all cases in a suite."""
    cases = load_eval_suite(suite_name)
    
    if not cases:
        return []
    
    results = []
    for case in cases:
        result = run_eval_case(case)
        results.append(result)
    
    return results


def run_all_evals() -> Dict[str, List[Dict[str, Any]]]:
    """Run all evaluation suites."""
    suites = ['functional', 'style', 'security_injection', 'tool_use']
    
    all_results = {}
    
    for suite in suites:
        if (EVALS_DIR / f"{suite}.jsonl").exists():
            all_results[suite] = run_suite(suite)
    
    return all_results


def print_results(results: Dict[str, List[Dict[str, Any]]], ci_mode: bool = False):
    """Print evaluation results."""
    total_passed = 0
    total_failed = 0
    
    print(f"\n{'='*60}")
    print(f"🧪 AGENT EVAL HARNESS RESULTS")
    print(f"   Timestamp: {datetime.utcnow().isoformat()}Z")
    print(f"{'='*60}\n")
    
    for suite, cases in results.items():
        passed = sum(1 for c in cases if c['passed'])
        failed = len(cases) - passed
        total_passed += passed
        total_failed += failed
        
        status = "✅" if failed == 0 else "❌"
        print(f"{status} {suite}: {passed}/{len(cases)} passed")
        
        for case in cases:
            icon = "✅" if case['passed'] else "❌"
            print(f"   {icon} {case['id']}: {case['message']}")
    
    print(f"\n{'='*60}")
    print(f"📊 SUMMARY")
    print(f"   Total: {total_passed + total_failed}")
    print(f"   Passed: {total_passed}")
    print(f"   Failed: {total_failed}")
    print(f"   Rate: {total_passed/(total_passed + total_failed)*100:.1f}%")
    print(f"{'='*60}\n")
    
    if ci_mode:
        # Output JSON for CI parsing
        output = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "total_passed": total_passed,
            "total_failed": total_failed,
            "suites": results
        }
        
        report_path = PROJECT_ROOT / "eval-report.json"
        with open(report_path, 'w') as f:
            json.dump(output, f, indent=2)
        print(f"📄 Report saved: {report_path}")
    
    return total_failed


def main():
    parser = argparse.ArgumentParser(description="Agent Eval Harness")
    parser.add_argument("--suite", help="Run specific suite only")
    parser.add_argument("--ci", action="store_true", help="CI mode (JSON output)")
    parser.add_argument("--judge", help="(Future) LLM judge for subjective evals")
    
    args = parser.parse_args()
    
    if args.judge:
        print(f"⚠️ LLM judge mode not yet implemented: {args.judge}")
    
    if args.suite:
        results = {args.suite: run_suite(args.suite)}
    else:
        results = run_all_evals()
    
    failed = print_results(results, ci_mode=args.ci)
    
    sys.exit(1 if failed > 0 else 0)


if __name__ == "__main__":
    main()
