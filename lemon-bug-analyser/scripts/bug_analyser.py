#!/usr/bin/env python3
"""Deterministic intake, report and audit helper for lemon-bug-analyser."""
import argparse
import json
import re
from pathlib import Path

REQUIRED_BUG = ("title", "actual", "expected")
VALID_STATES = {"candidate", "supported", "rejected", "verified", "inconclusive", "not-run"}

def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def intake(data):
    bug = data.setdefault("bug", {})
    missing = []
    for key in REQUIRED_BUG:
        if not bug.get(key):
            missing.append(key)
    if not bug.get("steps") and not bug.get("trigger_conditions"):
        missing.append("steps_or_trigger_conditions")
    if not bug.get("environment") or not bug.get("version"):
        missing.append("environment_or_version")
    data.setdefault("audit", {})["missing"] = missing
    data["audit"]["readiness"] = "READY" if not missing else "PARTIAL"
    data["audit"]["rules"] = [
        "Do not treat inferred content as observed fact",
        "Do not confirm a root cause without current verification evidence",
    ]
    return data

def validate(data):
    errors, warnings = [], []
    for i, h in enumerate(data.get("hypotheses", []), 1):
        hid = h.get("hypothesis_id", f"H-{i:03d}")
        if h.get("status") not in VALID_STATES:
            errors.append(f"{hid}: invalid status")
        if not h.get("supporting_evidence") and h.get("status") in {"supported", "verified"}:
            errors.append(f"{hid}: verified/support status needs evidence")
        if not h.get("verification_plan"):
            warnings.append(f"{hid}: missing verification plan")
    verified = {h.get("hypothesis_id") for h in data.get("hypotheses", []) if h.get("status") == "verified"}
    for root in data.get("conclusion", {}).get("root_causes", []):
        if root.get("hypothesis_id") not in verified:
            errors.append(f"root cause {root.get('hypothesis_id')} is not verified")
    for ev in data.get("evidence", []):
        if ev.get("fact_level") == "inferred" and ev.get("kind") in {"log", "api", "screenshot"}:
            warnings.append(f"{ev.get('evidence_id')}: inferred evidence is labelled as raw evidence")
    return {"valid": not errors, "errors": errors, "warnings": warnings}

def render(data):
    bug = data.get("bug", {})
    audit = data.get("audit", {})
    lines = ["# Bug Analysis Report", "", f"- Bug ID: `{bug.get('bug_id', 'unassigned')}`", f"- Title: {bug.get('title', '未提供')}", f"- Readiness: {audit.get('readiness', 'UNKNOWN')}", "", "## Observed behavior", "", f"- Actual: {bug.get('actual') or '待补充'}", f"- Expected: {bug.get('expected') or '待补充'}", "", "## Evidence", ""]
    for ev in data.get("evidence", []):
        lines.append(f"- **{ev.get('evidence_id', '?')}** [{ev.get('fact_level', 'unknown')}] {ev.get('content', '')} — {ev.get('source', 'unknown source')}")
    lines += ["", "## Hypotheses", "", "| ID | Claim | Status | Evidence |", "|---|---|---|---|"]
    for h in data.get("hypotheses", []):
        lines.append(f"| {h.get('hypothesis_id')} | {h.get('claim', '')} | {h.get('status', 'candidate')} | {', '.join(h.get('supporting_evidence', [])) or '待补充'} |")
    conclusion = data.get("conclusion", {})
    lines += ["", "## Decision", "", conclusion.get("summary", "当前不能确认根因；请先执行验证计划。"), "", "## Missing inputs", ""]
    lines += [f"- {x}" for x in audit.get("missing", [])] or ["- 无"]
    return "\n".join(lines) + "\n"

def orchestrate(data, matches=None):
    """Route history-first analysis without pretending a match is a diagnosis."""
    data = intake(data)
    matches = matches or []
    reliable = [m for m in matches if m.get("score", 0) >= 0.55 and not m.get("must_reverify")]
    data.setdefault("audit", {})["history_route"] = "history-candidate" if reliable else "professional-diagnosis"
    data["audit"]["history_candidates"] = [m.get("case_id") for m in matches[:5]]
    if reliable:
        data["audit"]["history_warning"] = "Historical cases are candidates; current evidence and verification remain required."
    else:
        data["audit"]["professional_route"] = ["classify domain", "build relationship chain", "generate falsifiable hypotheses", "schedule verification"]
    return data

def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="command", required=True)
    for name in ("intake", "report", "validate", "analyse"):
        sp = sub.add_parser(name); sp.add_argument("--input", required=True); sp.add_argument("--output"); sp.add_argument("--json")
        if name == "analyse": sp.add_argument("--history", help="optional history-match result JSON")
    args = p.parse_args(); data = load(args.input)
    if args.command == "intake":
        result = intake(data); text = json.dumps(result, ensure_ascii=False, indent=2)
    elif args.command == "validate":
        result = validate(data); text = json.dumps(result, ensure_ascii=False, indent=2)
    elif args.command == "analyse":
        matches = []
        if args.history:
            history = json.loads(Path(args.history).read_text(encoding="utf-8"))
            matches = history.get("matches", history if isinstance(history, list) else [])
        result = orchestrate(data, matches); text = json.dumps(result, ensure_ascii=False, indent=2)
    else:
        result = intake(data); text = render(result)
    if args.output: Path(args.output).write_text(text, encoding="utf-8")
    else: print(text)
    if args.json and args.command != "validate": Path(args.json).write_text(json.dumps(validate(data), ensure_ascii=False, indent=2), encoding="utf-8")

if __name__ == "__main__": main()
