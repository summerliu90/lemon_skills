#!/usr/bin/env python3
"""API coverage matrix and contract mutation helpers."""
from __future__ import annotations
import argparse, json, re, sys
from pathlib import Path
from typing import Any

def _load(path): return json.loads(Path(path).read_text(encoding="utf-8-sig"))
def _save(obj,path): Path(path).write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding="utf-8")

def matrix(doc):
    rows=[]
    for c in doc.get("testcases",[]):
        if c.get("kind")!="api": continue
        data=c.get("data",{}); tags=set(c.get("tags",[])); rows.append({"case_id":c.get("case_id"),"method":c.get("method"),"path":c.get("path"),"mode":next((x for x in ("valid","missing","empty","wrong_type","boundary","auth","negative") if x in tags),"other"),"has_status":bool(c.get("expected_status")),"has_source":bool(c.get("source_refs")),"has_assertion":bool(c.get("assertions")),"parameter_count":len(data) if isinstance(data,dict) else 0})
    return rows

def findings(doc):
    rows=matrix(doc); result=[]; groups={}
    for row in rows: groups.setdefault((row["method"],row["path"]),[]).append(row)
    for endpoint,cases in groups.items():
        modes={c["mode"] for c in cases}
        for required in ("valid","negative"):
            if required not in modes: result.append({"level":"warning","endpoint":endpoint,"code":"MISSING_MODE","message":f"缺少 {required} 覆盖"})
        if not any(c["has_status"] for c in cases): result.append({"level":"warning","endpoint":endpoint,"code":"NO_STATUS","message":"没有可验证的响应状态码"})
        if not any(c["has_assertion"] for c in cases): result.append({"level":"error","endpoint":endpoint,"code":"NO_ASSERTION","message":"没有响应断言"})
    return result

def mutate(case):
    variants=[]; original=case.get("data",{})
    if not isinstance(original,dict): return variants
    for key,value in original.items():
        clone=json.loads(json.dumps(case)); clone["case_id"]=f"{case.get('case_id')}-{len(variants)+1}"; clone["name"]=f"{case.get('name')} - 参数 {key} 异常"; clone.setdefault("tags",[]).append("mutation")
        if isinstance(value,bool): clone["data"][key]=not value
        elif isinstance(value,(int,float)): clone["data"][key]=value+1
        elif isinstance(value,str): clone["data"][key]=""
        else: clone["data"][key]=None
        clone["assertions"]=["系统拒绝不符合契约的参数并返回结构化错误响应"]; clone["priority"]="P1"; variants.append(clone)
    return variants

def expand(doc):
    result=json.loads(json.dumps(doc)); cases=list(result.get("testcases",[])); extra=[]
    for c in cases:
        if c.get("kind")=="api": extra.extend(mutate(c))
    result["testcases"]=cases+extra; return result

def main(argv=None):
    ap=argparse.ArgumentParser(); sub=ap.add_subparsers(dest="cmd",required=True); p=sub.add_parser("matrix"); p.add_argument("--input",required=True); p.add_argument("--output"); p=sub.add_parser("audit"); p.add_argument("--input",required=True); p.add_argument("--output"); p=sub.add_parser("mutate"); p.add_argument("--input",required=True); p.add_argument("--output",required=True); args=ap.parse_args(argv); doc=_load(args.input)
    if args.cmd=="matrix": out=matrix(doc); text=json.dumps(out,ensure_ascii=False,indent=2); Path(args.output).write_text(text,encoding="utf-8") if args.output else print(text)
    elif args.cmd=="audit": out=findings(doc); text=json.dumps(out,ensure_ascii=False,indent=2); Path(args.output).write_text(text,encoding="utf-8") if args.output else print(text); return 1 if any(x["level"]=="error" for x in out) else 0
    else: _save(expand(doc),args.output)
    return 0
if __name__=="__main__": sys.exit(main())
