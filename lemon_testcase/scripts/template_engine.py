#!/usr/bin/env python3
"""Template inheritance, auto-selection and field completion."""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]/"assets/templates"
def read(name):
    p=Path(name)
    if not p.exists():
        p=ROOT/(name if name.endswith(".json") else name+".json")
        if not p.exists() and name=="api": p=ROOT/"api-schema.json"
        if not p.exists() and name=="default": p=ROOT/"case-schema.json"
    if not p.exists(): raise FileNotFoundError(name)
    return json.loads(p.read_text(encoding="utf-8"))
def merge(parent,child):
    result=dict(parent); by={x.get("key"):x for x in parent.get("columns",[])}
    for col in child.get("columns",[]): by[col.get("key")]=col
    result.update(child); result["columns"]=list(by.values()); return result
def resolve(name):
    current=read(name); parent=current.get("inherits")
    return merge(resolve(parent),current) if parent else current
def choose(kind):
    return {"api":"api","ui":"ui","performance":"performance","automation":"automation"}.get(kind,"default")
def complete(doc,template):
    columns=resolve(template).get("columns",[]); cases=[]
    for case in doc.get("testcases",[]):
        item=dict(case)
        for col in columns:
            if col.get("key") not in item: item[col["key"]]=[] if col.get("key") in ("actions","assertions","preconditions","source_refs","notes") else ""
        cases.append(item)
    return {**doc,"template":template,"testcases":cases}
def main(argv=None):
    ap=argparse.ArgumentParser(); s=ap.add_subparsers(dest="cmd",required=True); r=s.add_parser("resolve"); r.add_argument("--name",required=True); c=s.add_parser("complete"); c.add_argument("--input",required=True); c.add_argument("--output",required=True); c.add_argument("--template"); args=ap.parse_args(argv)
    if args.cmd=="resolve": print(json.dumps(resolve(args.name),ensure_ascii=False,indent=2)); return 0
    doc=json.loads(Path(args.input).read_text(encoding="utf-8-sig")); template=args.template or choose(doc.get("testcases",[{}])[0].get("kind","functional")); Path(args.output).write_text(json.dumps(complete(doc,template),ensure_ascii=False,indent=2),encoding="utf-8"); print(f"template={template}"); return 0
if __name__=="__main__": sys.exit(main())
