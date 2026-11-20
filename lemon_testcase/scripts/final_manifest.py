#!/usr/bin/env python3
"""Produce the final capability, dependency and size manifest."""
from __future__ import annotations
import argparse,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def lines(patterns):
    total=0
    for pattern in patterns:
        for path in ROOT.glob(pattern):
            if path.is_file(): total+=len(path.read_text(encoding="utf-8").splitlines())
    return total
def manifest():
    scripts=sorted(str(p.relative_to(ROOT)) for p in (ROOT/"scripts").glob("*.py")); docs=sorted(str(p.relative_to(ROOT)) for p in ROOT.rglob("*.md")); templates=sorted(str(p.relative_to(ROOT)) for p in ROOT.glob("assets/templates/*"))
    return {"skill":"lemon_testcase","files":{"scripts":scripts,"references":docs,"templates":templates},"lines":{"all_text":lines(["SKILL.md","README.md","agents/*.yaml","scripts/*.py","references/*.md","assets/templates/*","examples/*.json"]),"python":lines(["scripts/*.py"]),"markdown":lines(["SKILL.md","README.md","references/*.md","assets/templates/*.md"])},"capabilities":{"inputs":["prd","markdown","txt","csv","docx","pdf","image","openapi","postman","online-text"],"generators":["functional","api","ui","performance","automation","state"],"outputs":["json","jsonl","markdown","csv","excel","xmind","html"],"quality":["contract","coverage","risk","security","roundtrip","dependency"]}}
def main(argv=None):
    ap=argparse.ArgumentParser(); ap.add_argument("--output"); args=ap.parse_args(argv); result=manifest(); text=json.dumps(result,ensure_ascii=False,indent=2); Path(args.output).write_text(text,encoding="utf-8") if args.output else print(text); return 0
if __name__=="__main__": sys.exit(main())
