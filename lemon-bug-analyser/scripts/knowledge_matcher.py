#!/usr/bin/env python3
"""Explainable, conservative matching for TestPilot historical cases."""
import argparse
import json
import re
from pathlib import Path

FIELDS = ("module", "business_flow", "environment", "version")

def tokens(value):
    return set(re.findall(r"[a-z0-9_./:-]+|[\u4e00-\u9fff]", str(value or "").lower()))

def overlap(left, right):
    a, b = tokens(left), tokens(right)
    return len(a & b) / max(len(a | b), 1)

def score(current, historical):
    matches, differences = [], []
    weighted = {"module": 0.24, "business_flow": 0.20, "api_signatures": 0.22, "conditions": 0.16, "environment": 0.08, "version_range": 0.05, "symptoms": 0.05}
    total = 0.0
    for field, weight in weighted.items():
        left = current.get(field) or current.get("bug", {}).get(field)
        right = historical.get(field)
        if field in {"api_signatures", "conditions", "symptoms", "version_range"}:
            left = " ".join(left or [])
            right = " ".join(right or [])
        value = overlap(left, right)
        total += value * weight
        (matches if value >= 0.35 else differences).append({"field": field, "similarity": round(value, 3)})
    quality = historical.get("quality", {})
    if quality.get("verification_complete") is True:
        total += 0.08
        matches.append({"field": "verification_quality", "similarity": 1.0})
    return {"case_id": historical.get("case_id"), "score": round(min(total, 1.0), 3), "matched_fields": matches, "different_fields": differences, "transferable_parts": historical.get("root_causes", []), "must_reverify": differences or not quality.get("verification_complete", False)}

def main():
    p = argparse.ArgumentParser(); p.add_argument("--current", required=True); p.add_argument("--history", required=True); p.add_argument("--output", required=True)
    a = p.parse_args(); current = json.loads(Path(a.current).read_text(encoding="utf-8")); history = json.loads(Path(a.history).read_text(encoding="utf-8")); cases = history if isinstance(history, list) else history.get("cases", [])
    result = sorted((score(current, case) for case in cases), key=lambda x: x["score"], reverse=True)
    Path(a.output).write_text(json.dumps({"matches": result, "policy": "similarity is candidate evidence, never a current root-cause confirmation"}, ensure_ascii=False, indent=2), encoding="utf-8")

if __name__ == "__main__": main()
