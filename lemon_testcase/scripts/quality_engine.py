#!/usr/bin/env python3
"""Extended quality engine: duplicate, secret, traceability and risk checks."""
from __future__ import annotations
import argparse, hashlib, json, re, sys
from pathlib import Path
from collections import defaultdict
from typing import Any

SECRET_PATTERNS=[(re.compile(r"(?i)(password|passwd|secret|token|api[_-]?key)\s*[:=]\s*[^\s,}]+"),"possible credential"),(re.compile(r"\b(?:sk|pk)[_-][A-Za-z0-9]{12,}\b"),"possible API key"),(re.compile(r"\b\d{15,19}\b"),"possible card/account number")]
VAGUE=re.compile(r"^(正常|符合预期|成功|正确|无异常|系统可用|提示正确|功能可用)[。！!。]?$",re.I)
def load(path): return json.loads(Path(path).read_text(encoding="utf-8-sig"))
def fingerprint(case):
    text="|".join([str(case.get("area","")),str(case.get("name",""))," ".join(map(str,case.get("actions",[])))," ".join(map(str,case.get("assertions",[])))])
    return hashlib.sha1(re.sub(r"\s+"," ",text.lower()).encode()).hexdigest()
def duplicate_findings(cases):
    groups=defaultdict(list)
    for c in cases: groups[fingerprint(c)].append(c.get("case_id",""))
    return [{"level":"warning","code":"DUPLICATE_CASE","case_ids":ids,"message":"案例内容高度相似"} for ids in groups.values() if len(ids)>1]
def secret_findings(cases):
    out=[]
    def scan(value,cid,location):
        text=json.dumps(value,ensure_ascii=False) if not isinstance(value,str) else value
        for pattern,label in SECRET_PATTERNS:
            if pattern.search(text): out.append({"level":"error","code":"SENSITIVE_DATA","case_id":cid,"location":location,"message":label})
    for c in cases:
        cid=c.get("case_id",""); scan(c.get("data",{}),cid,"data"); scan(c.get("actions",[]),cid,"actions"); scan(c.get("assertions",[]),cid,"assertions")
    return out
def trace_findings(cases):
    out=[]
    for c in cases:
        cid=c.get("case_id","")
        if not c.get("source_refs"): out.append({"level":"warning","code":"UNTRACEABLE","case_id":cid,"message":"没有来源引用"})
        if any(VAGUE.match(str(x).strip()) for x in c.get("assertions",[])): out.append({"level":"warning","code":"VAGUE_ASSERTION","case_id":cid,"message":"预期结果过于模糊"})
        if len(c.get("actions",[]))<1: out.append({"level":"error","code":"NO_ACTION","case_id":cid,"message":"缺少可执行步骤"})
    return out
def risk_summary(cases):
    result={"p0":0,"p1":0,"negative":0,"boundary":0,"state":0,"auth":0,"automation":0}
    for c in cases:
        p=str(c.get("priority","")).lower(); result[p]=result.get(p,0)+1
        for tag in ("negative","boundary","state","auth"):
            if tag in c.get("tags",[]): result[tag]+=1
        if c.get("automation_candidate"): result["automation"]+=1
    return result
def run(doc):
    cases=doc.get("testcases",[]); findings=duplicate_findings(cases)+secret_findings(cases)+trace_findings(cases); return {"valid":not any(x["level"]=="error" for x in findings),"risk_summary":risk_summary(cases),"findings":findings,"case_count":len(cases)}
def main(argv=None):
    ap=argparse.ArgumentParser(); ap.add_argument("--input",required=True); ap.add_argument("--output"); args=ap.parse_args(argv); result=run(load(args.input)); text=json.dumps(result,ensure_ascii=False,indent=2)
    if args.output: Path(args.output).write_text(text,encoding="utf-8")
    else: print(text)
    return 1 if not result["valid"] else 0
if __name__=="__main__": sys.exit(main())
