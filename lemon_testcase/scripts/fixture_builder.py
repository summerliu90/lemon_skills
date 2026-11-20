#!/usr/bin/env python3
"""Build deterministic test-data fixtures from a canonical case document."""
from __future__ import annotations
import argparse, json, sys, uuid
from pathlib import Path
def read(p): return json.loads(Path(p).read_text(encoding="utf-8-sig"))
def value(seed,key,index):
    if key.lower().endswith("email"): return f"lemon.{seed}.{index}@example.test"
    if "id" in key.lower(): return f"fixture-{seed}-{index}"
    if "token" in key.lower(): return f"test-token-{seed}-{index}"
    return f"sample-{seed}-{index}"
def build(doc, seed="001"):
    fixtures=[]
    for i,case in enumerate(doc.get("testcases",[]),1):
        data=case.get("data",{}); generated={}
        if isinstance(data,dict):
            for key,val in data.items():
                if isinstance(val,str) and (val.startswith("${") or val in ("sample","__variable__")): generated[key]=value(seed,key,i)
                else: generated[key]=val
        fixtures.append({"case_id":case.get("case_id"),"fixture_id":f"fx-{seed}-{i:04d}","data":generated,"cleanup":["删除本案例创建的资源","撤销临时认证凭证"],"isolation":"per-case"})
    return {"schema_version":"1.0","seed":seed,"fixtures":fixtures}
def main(argv=None):
    ap=argparse.ArgumentParser(); ap.add_argument("--input",required=True); ap.add_argument("--output",required=True); ap.add_argument("--seed",default="001"); args=ap.parse_args(argv); Path(args.output).write_text(json.dumps(build(read(args.input),args.seed),ensure_ascii=False,indent=2),encoding="utf-8"); print(f"built fixtures -> {args.output}")
if __name__=="__main__": sys.exit(main())
