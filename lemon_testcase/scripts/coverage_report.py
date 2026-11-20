#!/usr/bin/env python3
"""Emit a machine-readable coverage summary for delivery manifests."""
import argparse,json,sys
from pathlib import Path
def main(argv=None):
    ap=argparse.ArgumentParser(); ap.add_argument("--input",required=True); ap.add_argument("--output"); args=ap.parse_args(argv); doc=json.loads(Path(args.input).read_text(encoding="utf-8-sig")); cases=doc.get("testcases",[]); areas=sorted({x.get("area","") for x in cases}); result={"case_count":len(cases),"areas":areas,"area_count":len(areas),"positive":sum("positive" in x.get("tags",[]) for x in cases),"negative":sum("negative" in x.get("tags",[]) for x in cases),"boundary":sum("boundary" in x.get("tags",[]) for x in cases),"state":sum("state" in x.get("tags",[]) for x in cases),"source_coverage":sum(bool(x.get("source_refs")) for x in cases)/len(cases) if cases else 0}; text=json.dumps(result,ensure_ascii=False,indent=2); Path(args.output).write_text(text,encoding="utf-8") if args.output else print(text)
if __name__=="__main__": sys.exit(main())
