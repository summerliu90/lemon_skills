#!/usr/bin/env python3
"""Schema-oriented validator for generated case documents."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
from typing import Any

REQUIRED=("case_id","name","area","kind","priority","preconditions","actions","assertions")
LIST_FIELDS=("preconditions","actions","assertions","source_refs","tags","notes")
KNOWN_KINDS={"functional","api","ui","performance","automation"}
def load(path): return json.loads(Path(path).read_text(encoding="utf-8-sig"))
def add(items,level,code,message,path=""): items.append({"level":level,"code":code,"path":path,"message":message})
def validate(doc):
    errors=[]
    if not isinstance(doc,dict): add(errors,"error","ROOT_TYPE","文档必须是对象"); return errors
    if not isinstance(doc.get("testcases"),list): add(errors,"error","CASES_TYPE","testcases 必须是数组"); return errors
    if doc.get("schema_version") is None: add(errors,"warning","NO_VERSION","缺少 schema_version")
    seen=set()
    for index,case in enumerate(doc["testcases"]):
        path=f"testcases[{index}]"; cid=case.get("case_id","") if isinstance(case,dict) else ""
        if not isinstance(case,dict): add(errors,"error","CASE_TYPE","案例必须是对象",path); continue
        if cid in seen: add(errors,"error","DUPLICATE_ID",f"重复编号 {cid}",path)
        seen.add(cid)
        for key in REQUIRED:
            if key not in case: add(errors,"error","MISSING_FIELD",f"缺少 {key}",path)
        if case.get("kind") not in KNOWN_KINDS: add(errors,"warning","UNKNOWN_KIND",str(case.get("kind")),path)
        if case.get("priority") not in ("P0","P1","P2","P3"): add(errors,"error","BAD_PRIORITY",str(case.get("priority")),path)
        for key in LIST_FIELDS:
            if key in case and not isinstance(case[key],list): add(errors,"error","BAD_LIST",key,path)
        if case.get("kind")=="api":
            if not case.get("method"): add(errors,"warning","API_METHOD","API 案例缺少 method",path)
            if not case.get("path"): add(errors,"warning","API_PATH","API 案例缺少 path",path)
            if "expected_status" in case and not isinstance(case["expected_status"],list): add(errors,"error","BAD_STATUS","expected_status 必须是数组",path)
        if case.get("automation_candidate") and not case.get("assertions"): add(errors,"warning","AUTOMATION_ASSERTION","自动化候选缺少断言",path)
    return errors
def main(argv=None):
    ap=argparse.ArgumentParser(); ap.add_argument("--input",required=True); ap.add_argument("--output"); args=ap.parse_args(argv); errors=validate(load(args.input)); result={"valid":not any(x["level"]=="error" for x in errors),"errors":errors}; text=json.dumps(result,ensure_ascii=False,indent=2); Path(args.output).write_text(text,encoding="utf-8") if args.output else print(text); return 1 if not result["valid"] else 0
if __name__=="__main__": sys.exit(main())
