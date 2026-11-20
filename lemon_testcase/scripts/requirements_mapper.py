#!/usr/bin/env python3
"""Map requirement records to cases and emit a coverage report."""
from __future__ import annotations
import argparse, json, re, sys
from pathlib import Path
def read(path): return json.loads(Path(path).read_text(encoding="utf-8-sig"))
def tokens(text): return set(x.lower() for x in re.findall(r"[A-Za-z0-9_\u4e00-\u9fff]{2,}",str(text)))
def map_requirements(doc, requirements):
    cases=doc.get("testcases",[]); result=[]
    for req in requirements:
        rid=str(req.get("id", "")); wanted=tokens(req.get("text", "")); hits=[]
        for c in cases:
            sources=" ".join(map(str,c.get("source_refs",[]))); words=tokens(" ".join([c.get("name",""),c.get("area",""),sources]))
            score=len(wanted & words) if wanted else 0
            if rid and rid in sources: score+=10
            if score>0: hits.append({"case_id":c.get("case_id"),"score":score})
        hits.sort(key=lambda x:x["score"],reverse=True); result.append({"requirement_id":rid,"text":req.get("text",""),"covered":bool(hits),"matches":hits[:10]})
    return result
def main(argv=None):
    ap=argparse.ArgumentParser(); ap.add_argument("--cases",required=True); ap.add_argument("--requirements",required=True); ap.add_argument("--output"); args=ap.parse_args(argv); report=map_requirements(read(args.cases),read(args.requirements)); out={"total":len(report),"covered":sum(x["covered"] for x in report),"uncovered":[x["requirement_id"] for x in report if not x["covered"]],"items":report}; text=json.dumps(out,ensure_ascii=False,indent=2); Path(args.output).write_text(text,encoding="utf-8") if args.output else print(text); return 1 if out["uncovered"] else 0
if __name__=="__main__": sys.exit(main())
