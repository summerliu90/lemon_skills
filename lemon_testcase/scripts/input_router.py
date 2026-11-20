#!/usr/bin/env python3
"""Explain source and output routing decisions before execution."""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
def route(path,requested=None):
    ext=Path(path).suffix.lower(); source={".docx":"docx",".pdf":"pdf",".csv":"csv",".md":"markdown",".markdown":"markdown",".txt":"text",".yaml":"openapi-yaml",".yml":"openapi-yaml",".json":"json",".png":"ui-image",".jpg":"ui-image",".jpeg":"ui-image",".webp":"ui-image"}.get(ext,"unknown")
    outputs={"docx":"functional","pdf":"functional","csv":"imported","markdown":"functional","text":"functional","openapi-yaml":"api","json":"api-or-postman","ui-image":"ui"}; kind=requested or outputs.get(source,"functional"); template={"api":"api","ui":"ui","performance":"performance","automation":"automation"}.get(kind,"default")
    return {"input":path,"extension":ext,"source_kind":source,"test_kind":kind,"template":template,"next":"canonical JSON -> quality check -> requested renderer"}
def main(argv=None):
    ap=argparse.ArgumentParser(); ap.add_argument("--input",required=True); ap.add_argument("--kind"); args=ap.parse_args(argv); print(json.dumps(route(args.input,args.kind),ensure_ascii=False,indent=2)); return 0
if __name__=="__main__": sys.exit(main())
