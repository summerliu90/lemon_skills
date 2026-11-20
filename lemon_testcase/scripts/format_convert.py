#!/usr/bin/env python3
"""Compatibility-style conversion facade with explicit format validation."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
from lemon_cases import load, render_table, render_xmind
def main(argv=None):
    ap=argparse.ArgumentParser(); ap.add_argument("--input",required=True); ap.add_argument("--output",required=True); ap.add_argument("--to",choices=["excel","json","markdown","csv","xmind"],required=True); ap.add_argument("--title",default="测试用例"); ap.add_argument("--template",default="default"); args=ap.parse_args(argv); doc=load(args.input)
    if args.to=="excel":
        from excel_bridge import export_json
        export_json(doc,args.output,args.template)
        print(f"converted {len(doc['testcases'])} cases -> {args.output}")
        return 0
    if args.to=="json": result=json.dumps(doc,ensure_ascii=False,indent=2); Path(args.output).write_text(result,encoding="utf-8")
    elif args.to=="markdown": Path(args.output).write_text(render_table(doc,args.template),encoding="utf-8")
    elif args.to=="xmind": render_xmind(doc,args.output,args.title)
    else:
        from lemon_cases import read_template, scalar
        import csv
        with open(args.output,"w",encoding="utf-8-sig",newline="") as f:
            w=csv.writer(f); cols=read_template(args.template); w.writerow([x["label"] for x in cols]); w.writerows([[scalar(c.get(x["key"],"")) for x in cols] for c in doc["testcases"]])
    print(f"converted {len(doc['testcases'])} cases -> {args.output}")
if __name__=="__main__": main()
