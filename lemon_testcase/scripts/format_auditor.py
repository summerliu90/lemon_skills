#!/usr/bin/env python3
"""Audit XMind package invariants."""
from __future__ import annotations
import argparse,json,re,sys,zipfile
from pathlib import Path
def xmind(path):
    errors=[]
    try:
        with zipfile.ZipFile(path) as archive:
            names=set(archive.namelist()); required={"content.json","manifest.json","metadata.json"}; missing=required-names
            if missing: errors.append("缺少: "+", ".join(sorted(missing)))
            if "content.json" in names:
                data=json.loads(archive.read("content.json"));
                if not isinstance(data,list) or not data: errors.append("content.json 根结构无效")
    except Exception as exc: errors.append(str(exc))
    return {"format":"xmind","valid":not errors,"errors":errors}
def main(argv=None):
    ap=argparse.ArgumentParser(); ap.add_argument("--input",required=True); ap.add_argument("--format",choices=["xmind"],required=True); args=ap.parse_args(argv); result=xmind(args.input); print(json.dumps(result,ensure_ascii=False,indent=2)); return 0 if result["valid"] else 1
if __name__=="__main__": sys.exit(main())
