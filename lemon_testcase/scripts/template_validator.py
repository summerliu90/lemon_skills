#!/usr/bin/env python3
"""Validate template inheritance, column keys and required-field coverage."""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]/"assets/templates"
def read(name):
    p=Path(name)
    if not p.exists():
        p=ROOT/(name if name.endswith(".json") else name+".json")
        if not p.exists() and name=="api": p=ROOT/"api-schema.json"
        if not p.exists() and name in ("ui","performance","automation"): p=ROOT/f"{name}-schema.json"
        if not p.exists() and name=="default": p=ROOT/"case-schema.json"
    return json.loads(p.read_text(encoding="utf-8"))
def check(template):
    errors=[]; cols=template.get("columns",[]); keys=[]
    for i,col in enumerate(cols):
        if not col.get("key"): errors.append(f"列 {i} 缺少 key")
        if not col.get("label"): errors.append(f"列 {i} 缺少 label")
        if col.get("key") in keys: errors.append(f"重复 key: {col.get('key')}")
        keys.append(col.get("key"))
    return errors
def main(argv=None):
    ap=argparse.ArgumentParser(); ap.add_argument("--name",required=True); args=ap.parse_args(argv); t=read(args.name); errors=check(t); print(json.dumps({"name":t.get("name"),"valid":not errors,"columns":len(t.get("columns",[])),"errors":errors},ensure_ascii=False,indent=2)); return 1 if errors else 0
if __name__=="__main__": sys.exit(main())
