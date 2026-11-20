#!/usr/bin/env python3
"""Batch round-trip checks for representative canonical documents."""
from __future__ import annotations
import argparse,json,sys,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from lemon_cases import load,render_table,from_markdown,render_xmind
def run(path):
    doc=load(path); original=[x.get("case_id") for x in doc.get("testcases",[])]; results={}
    table=from_markdown(render_table(doc)); results["markdown"]={"count":len(table["testcases"]),"same":len(table["testcases"])==len(original)}
    with tempfile.NamedTemporaryFile(suffix=".xmind") as handle:
        render_xmind(doc,handle.name); results["xmind"]={"bytes":Path(handle.name).stat().st_size,"same":Path(handle.name).stat().st_size>0}
    return {"input":path,"input_count":len(original),"results":results,"valid":all(x["same"] for x in results.values())}
def main(argv=None):
    ap=argparse.ArgumentParser(); ap.add_argument("inputs",nargs="+"); args=ap.parse_args(argv); reports=[run(x) for x in args.inputs]; print(json.dumps({"valid":all(x["valid"] for x in reports),"reports":reports},ensure_ascii=False,indent=2)); return 0 if all(x["valid"] for x in reports) else 1
if __name__=="__main__": sys.exit(main())
