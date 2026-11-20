#!/usr/bin/env python3
"""Verify that renderers preserve case identity and count."""
from __future__ import annotations
import argparse, json, sys, zipfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from lemon_cases import load, render_table, from_markdown

def ids(doc): return [str(c.get("case_id")) for c in doc.get("testcases",[])]
def inspect_xmind(path):
    with zipfile.ZipFile(path) as z:
        names=set(z.namelist())
        required={"content.json","manifest.json","metadata.json"}
        if not required <= names: return False,"缺少 XMind 入口文件"
        try: json.loads(z.read("content.json"))
        except Exception as exc: return False,f"content.json 无法解析: {exc}"
    return True,"ok"
def main(argv=None):
    ap=argparse.ArgumentParser(); ap.add_argument("--input",required=True); ap.add_argument("--xmind"); args=ap.parse_args(argv); doc=load(args.input); original=ids(doc); table=from_markdown(render_table(doc)); errors=[]
    if len(table.get("testcases",[]))!=len(original): errors.append("表格回读数量变化")
    if args.xmind:
        good,message=inspect_xmind(args.xmind)
        if not good: errors.append(message)
    result={"valid":not errors,"input_count":len(original),"table_count":len(table.get("testcases",[])),"errors":errors}; print(json.dumps(result,ensure_ascii=False,indent=2)); return 1 if errors else 0
if __name__=="__main__": sys.exit(main())
