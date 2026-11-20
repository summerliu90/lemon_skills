#!/usr/bin/env python3
"""Small source adapters for text, CSV and legacy case JSON.

The adapter intentionally does not pretend to understand binary documents or
images.  Those inputs should first be extracted by the host environment; this
module then makes the extracted material canonical and traceable.
"""
from __future__ import annotations
import argparse, csv, json, re, sys
from pathlib import Path
from typing import Any

def split_text(value: Any) -> list[str]:
    if value is None: return []
    if isinstance(value,list): return [str(x).strip() for x in value if str(x).strip()]
    return [x.strip() for x in re.split(r"\r?\n|<br\s*/?>",str(value)) if x.strip()]

def map_key(key: str) -> str:
    aliases={"用例编号":"case_id","用例ID":"case_id","用例名称":"name","用例标题":"name","模块":"area","所属模块":"area","类别":"kind","测试类型":"kind","优先级":"priority","前置条件":"preconditions","前置操作":"preconditions","测试步骤":"actions","执行步骤":"actions","预期结果":"assertions","测试数据":"data","依据":"source_refs","需求依据":"source_refs"}
    return aliases.get(key.strip(),key.strip().lower().replace(" ","_"))

def convert_row(row: dict[str,Any], number: int) -> dict[str,Any]:
    d={map_key(k):v for k,v in row.items()}; cid=str(d.get("case_id") or f"LM-IMP-{number:04d}")
    return {"case_id":cid,"name":str(d.get("name") or "导入案例"),"area":str(d.get("area") or "导入模块"),"kind":str(d.get("kind") or "functional"),"priority":str(d.get("priority") or "P2"),"preconditions":split_text(d.get("preconditions")),"actions":split_text(d.get("actions")),"assertions":split_text(d.get("assertions")),"data":d.get("data") or {},"source_refs":split_text(d.get("source_refs")),"tags":split_text(d.get("tags")),"notes":split_text(d.get("notes")),"automation_candidate":str(d.get("automation_candidate","")).lower() in ("true","yes","1","是","✓")}

def from_csv(path: str) -> list[dict[str,Any]]:
    with open(path,encoding="utf-8-sig",newline="") as f: return [convert_row(row,i) for i,row in enumerate(csv.DictReader(f),1)]

def from_json(path: str) -> list[dict[str,Any]]:
    obj=json.loads(Path(path).read_text(encoding="utf-8-sig")); rows=obj if isinstance(obj,list) else obj.get("testcases",obj.get("cases",[])); return [convert_row(x,i) for i,x in enumerate(rows,1)]

def from_markdown(path: str) -> list[dict[str,Any]]:
    rows=[]
    for line in Path(path).read_text(encoding="utf-8-sig").splitlines():
        if "|" not in line or set(line.replace("|","").replace("-","").replace(":","").strip())==set(): continue
        cells=[x.strip() for x in line.strip().strip("|").split("|")]; rows.append(cells)
    if len(rows)<2: return []
    headers=rows[0]; return [convert_row(dict(zip(headers,row)),i) for i,row in enumerate(rows[2:],1) if len(row)>=len(headers)]

def main(argv=None):
    ap=argparse.ArgumentParser(); ap.add_argument("--input",required=True); ap.add_argument("--output",required=True); ap.add_argument("--project",default=""); args=ap.parse_args(argv); ext=Path(args.input).suffix.lower()
    cases=from_json(args.input) if ext==".json" else from_csv(args.input) if ext==".csv" else from_markdown(args.input)
    Path(args.output).write_text(json.dumps({"schema_version":"1.0","project":args.project,"source":{"kind":"imported","files":[args.input]},"assumptions":[],"testcases":cases},ensure_ascii=False,indent=2),encoding="utf-8"); print(f"imported {len(cases)} cases")
if __name__=="__main__": sys.exit(main())
