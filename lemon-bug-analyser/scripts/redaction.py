#!/usr/bin/env python3
"""Conservative redaction for logs and reports before knowledge-base reuse."""
import argparse
import json
import re
from pathlib import Path

PATTERNS = [
    ("email", re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b")),
    ("bearer", re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+")),
    ("secret_assignment", re.compile(r"(?i)\b(api[_-]?key|token|secret|password)\s*[:=]\s*[^\s,;]+")),
    ("phone", re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)")),
    ("ipv4", re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")),
]

def redact(text):
    hits = []
    for name, pattern in PATTERNS:
        text, count = pattern.subn(f"<{name}:REDACTED>", text)
        if count: hits.append({"kind": name, "count": count})
    return text, hits

def walk(value, hits):
    if isinstance(value, str):
        result, found = redact(value); hits.extend(found); return result
    if isinstance(value, list): return [walk(x, hits) for x in value]
    if isinstance(value, dict): return {k: walk(v, hits) for k, v in value.items()}
    return value

def main():
    p = argparse.ArgumentParser(); p.add_argument("--input", required=True); p.add_argument("--output", required=True); p.add_argument("--audit", required=True)
    a = p.parse_args(); raw = json.loads(Path(a.input).read_text(encoding="utf-8")); hits = []; safe = walk(raw, hits)
    Path(a.output).write_text(json.dumps(safe, ensure_ascii=False, indent=2), encoding="utf-8"); Path(a.audit).write_text(json.dumps({"redacted": bool(hits), "hits": hits}, ensure_ascii=False, indent=2), encoding="utf-8")

if __name__ == "__main__": main()
