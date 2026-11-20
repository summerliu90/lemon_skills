#!/usr/bin/env python3
"""Compare two canonical inventories by identity and semantic fields."""
import argparse,json,sys
from pathlib import Path
def read(path): return json.loads(Path(path).read_text(encoding="utf-8-sig"))
def diff(left,right):
    a={x.get("case_id"):x for x in left.get("testcases",[])}; b={x.get("case_id"):x for x in right.get("testcases",[])}; added=sorted(set(b)-set(a)); removed=sorted(set(a)-set(b)); changed=[]
    for key in sorted(set(a)&set(b)):
        fields=[]
        for name in ("name","area","kind","priority","preconditions","actions","assertions","source_refs"):
            if a[key].get(name)!=b[key].get(name): fields.append(name)
        if fields: changed.append({"case_id":key,"fields":fields})
    return {"added":added,"removed":removed,"changed":changed,"same":not added and not removed and not changed}
def summary(result):
    return {"added_count":len(result["added"]),"removed_count":len(result["removed"]),"changed_count":len(result["changed"]),"same":result["same"]}
def main(argv=None):
    ap=argparse.ArgumentParser(); ap.add_argument("--before",required=True); ap.add_argument("--after",required=True); ap.add_argument("--output"); ap.add_argument("--summary",action="store_true"); args=ap.parse_args(argv); result=diff(read(args.before),read(args.after)); payload=summary(result) if args.summary else result; text=json.dumps(payload,ensure_ascii=False,indent=2); Path(args.output).write_text(text,encoding="utf-8") if args.output else print(text); return 0
if __name__=="__main__": sys.exit(main())
