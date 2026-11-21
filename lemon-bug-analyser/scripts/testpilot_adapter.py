#!/usr/bin/env python3
"""Normalize common TestPilot exports without making business assumptions."""
import argparse
import json
from pathlib import Path

def _first(obj, *keys):
    for key in keys:
        value = obj.get(key)
        if value not in (None, "", []):
            return value
    return None

def normalize(raw):
    run = raw.get("run", raw.get("execution", raw))
    bug = raw.get("bug", {})
    context = raw.get("context", {})
    steps = _first(bug, "steps", "reproduction_steps") or _first(run, "steps", "actions") or []
    attachments = _first(run, "attachments", "artifacts") or []
    evidence = []
    for index, item in enumerate(attachments, 1):
        if isinstance(item, str):
            item = {"path": item}
        evidence.append({
            "evidence_id": f"TP-E-{index:03d}",
            "kind": item.get("kind", "artifact"),
            "content": item.get("summary", item.get("path", "")),
            "source": item.get("source", "TestPilot export"),
            "locator": item.get("path"),
            "fact_level": "observed",
            "reliability": item.get("reliability", "medium"),
            "entities": item.get("entities", []),
            "supports": [],
            "contradicts": []
        })
    return {
        "schema_version": "1.0",
        "bug": {
            "bug_id": _first(bug, "bug_id", "id") or _first(run, "bug_id", "id"),
            "title": _first(bug, "title", "name") or _first(run, "title", "name"),
            "description": _first(bug, "description", "summary"),
            "actual": _first(bug, "actual", "actual_result") or _first(run, "actual", "failure_message"),
            "expected": _first(bug, "expected", "expected_result") or _first(run, "expected"),
            "steps": steps,
            "trigger_conditions": _first(bug, "trigger_conditions") or [],
            "project": _first(context, "project") or _first(run, "project"),
            "module": _first(bug, "module", "area") or _first(context, "module"),
            "business_flow": _first(context, "business_flow", "flow"),
            "environment": _first(context, "environment") or _first(run, "environment"),
            "version": _first(context, "version", "build") or _first(run, "version", "build"),
            "occurred_at": _first(run, "occurred_at", "started_at"),
            "frequency": _first(bug, "frequency") or "unknown",
            "report_source": "testpilot"
        },
        "context": {"test_case": _first(run, "test_case", "case_id"), "run_id": _first(run, "run_id", "execution_id")},
        "evidence": evidence,
        "relationships": raw.get("relationships", []),
        "history_matches": raw.get("history_matches", []),
        "hypotheses": raw.get("hypotheses", []),
        "verifications": raw.get("verifications", []),
        "conclusion": raw.get("conclusion", {}),
        "remediation": raw.get("remediation", {}),
        "regression": raw.get("regression", {}),
        "audit": {"source_adapter": "testpilot_adapter", "missing": []}
    }

def main():
    p = argparse.ArgumentParser(); p.add_argument("--input", required=True); p.add_argument("--output", required=True)
    a = p.parse_args(); raw = json.loads(Path(a.input).read_text(encoding="utf-8")); Path(a.output).write_text(json.dumps(normalize(raw), ensure_ascii=False, indent=2), encoding="utf-8")

if __name__ == "__main__": main()
