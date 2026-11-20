#!/usr/bin/env python3
"""Security-oriented case augmentation and output redaction."""
from __future__ import annotations
import argparse,json,re,sys
from pathlib import Path
PATTERNS=[(re.compile(r"(?i)(password|passwd|secret|token|api[_-]?key)(\s*[:=]\s*)([^\s,}]+)"),r"\1\2<redacted>"),(re.compile(r"\b\d{15,19}\b"),"<redacted-number>"),(re.compile(r"(?i)bearer\s+[A-Za-z0-9._-]+"),"Bearer <redacted>")]
def read(path): return json.loads(Path(path).read_text(encoding="utf-8-sig"))
def redact(value):
    if isinstance(value,str):
        for pattern,replacement in PATTERNS: value=pattern.sub(replacement,value)
        return value
    if isinstance(value,list): return [redact(x) for x in value]
    if isinstance(value,dict): return {k:redact(v) for k,v in value.items()}
    return value
def augment(doc):
    result=json.loads(json.dumps(doc));
    for case in result.get("testcases",[]):
        if case.get("kind") in ("api","functional"):
            case.setdefault("tags",[])
            if "auth" not in case["tags"]: case["tags"].append("security-review")
            case.setdefault("notes",[]).append("检查未授权、越权、敏感信息泄露和日志脱敏")
    return redact(result)
def main(argv=None):
    ap=argparse.ArgumentParser(); ap.add_argument("--input",required=True); ap.add_argument("--output",required=True); args=ap.parse_args(argv); Path(args.output).write_text(json.dumps(augment(read(args.input)),ensure_ascii=False,indent=2),encoding="utf-8"); print(f"security augmented -> {args.output}")
if __name__=="__main__": sys.exit(main())
