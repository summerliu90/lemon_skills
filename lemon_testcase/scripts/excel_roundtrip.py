#!/usr/bin/env python3
"""Excel export/import verification with controlled dependency diagnostics."""
from __future__ import annotations
import argparse,json,sys,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from excel_bridge import export_json,import_xlsx
from template_engine import resolve
def compare(before,after):
    left={str(x.get("case_id")):x for x in before.get("testcases",[])}; right={str(x.get("case_id")):x for x in after.get("testcases",[])}; missing=sorted(set(left)-set(right)); extra=sorted(set(right)-set(left)); fields=[]
    for key in sorted(set(left)&set(right)):
        for field in ("case_id","name","area","test_method","priority"):
            if str(left[key].get(field,""))!=str(right[key].get(field,"")): fields.append({"case_id":key,"field":field})
    return {"same_count":len(left)==len(right),"input_count":len(left),"output_count":len(right),"missing":missing,"extra":extra,"changed_identity":fields,"valid":not missing and not extra and not fields}
def main(argv=None):
    ap=argparse.ArgumentParser(); ap.add_argument("--input",required=True); ap.add_argument("--template",default="default"); ap.add_argument("--output"); args=ap.parse_args(argv)
    try:
        before=json.loads(Path(args.input).read_text(encoding="utf-8-sig"))
        with tempfile.TemporaryDirectory() as directory:
            workbook=str(Path(directory)/"roundtrip.xlsx"); export_json(before,workbook,args.template); after=import_xlsx(workbook,args.template); result=compare(before,after)
    except ImportError: result={"valid":False,"dependency":"openpyxl","message":"安装 openpyxl 后才能执行 Excel 往返检查"}
    text=json.dumps(result,ensure_ascii=False,indent=2); Path(args.output).write_text(text,encoding="utf-8") if args.output else print(text); return 0 if result.get("valid") else 1
if __name__=="__main__": sys.exit(main())
