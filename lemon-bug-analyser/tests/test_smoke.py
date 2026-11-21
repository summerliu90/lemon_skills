#!/usr/bin/env python3
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"

def run(*args):
    return subprocess.run([sys.executable, *args], cwd=ROOT, text=True, capture_output=True, check=True)

def test_examples_are_valid():
    for path in sorted((ROOT / "examples").glob("*.json")):
        result = run(str(SCRIPTS / "bug_analyser.py"), "validate", "--input", str(path))
        assert '"valid": true' in result.stdout

def test_testpilot_adapter_and_redaction():
    with tempfile.TemporaryDirectory() as tmp:
        src = ROOT / "examples" / "frontend-white-screen.json"
        context = Path(tmp) / "context.json"
        safe = Path(tmp) / "safe.json"
        audit = Path(tmp) / "audit.json"
        run(str(SCRIPTS / "testpilot_adapter.py"), "--input", str(src), "--output", str(context))
        data = json.loads(context.read_text())
        assert data["bug"]["report_source"] == "testpilot"
        run(str(SCRIPTS / "redaction.py"), "--input", str(context), "--output", str(safe), "--audit", str(audit))
        assert json.loads(audit.read_text())["redacted"] is False

def test_report_is_not_confirmation_without_verified_hypothesis():
    result = run(str(SCRIPTS / "bug_analyser.py"), "report", "--input", str(ROOT / "examples" / "ai-context-loss.json"))
    assert "不能确认根因" in result.stdout

if __name__ == "__main__":
    test_examples_are_valid(); test_testpilot_adapter_and_redaction(); print("smoke tests passed")
