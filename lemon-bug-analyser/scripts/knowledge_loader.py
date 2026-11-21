#!/usr/bin/env python3
"""Build a conservative local index from JSON/NDJSON TestPilot knowledge exports."""
import argparse
import json
from pathlib import Path

def load_file(path):
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".ndjson":
        return [json.loads(line) for line in text.splitlines() if line.strip()]
    value = json.loads(text)
    if isinstance(value, list): return value
    return value.get("cases", value.get("items", [value]))

def build(root):
    cases, sources, errors = [], [], []
    for path in sorted(Path(root).rglob("*")):
        if path.suffix.lower() not in {".json", ".ndjson"}: continue
        try:
            items = load_file(path)
            for item in items:
                if not isinstance(item, dict): continue
                item.setdefault("source_file", str(path))
                cases.append(item)
            sources.append(str(path))
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            errors.append({"file": str(path), "error": str(exc)})
    return {"schema_version": "1.0", "cases": cases, "index": {"source_files": sources, "errors": errors, "case_count": len(cases)}}

def main():
    p = argparse.ArgumentParser(); p.add_argument("--root", required=True); p.add_argument("--output", required=True)
    a = p.parse_args(); Path(a.output).write_text(json.dumps(build(a.root), ensure_ascii=False, indent=2), encoding="utf-8")

if __name__ == "__main__": main()
