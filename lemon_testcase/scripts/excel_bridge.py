#!/usr/bin/env python3
"""Excel bridge for Lemon cases.

The dependency is optional.  When openpyxl is present this module preserves
the column order supplied by a JSON template, writes readable multi-line cells,
freezes the header and applies filters.  It never overwrites the input file.
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
try:
    from openpyxl import Workbook, load_workbook
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter
except ImportError:
    Workbook = None

BASE=Path(__file__).resolve().parents[1]; TEMPLATE=BASE/"assets/templates"
def template(name):
    p=Path(name); p=p if p.exists() else TEMPLATE/(name if name.endswith(".json") else name+".json")
    if not p.exists(): p=TEMPLATE/"case-schema.json"
    return json.loads(p.read_text(encoding="utf-8"))
def read_doc(path): return json.loads(Path(path).read_text(encoding="utf-8-sig"))
def text(value):
    if isinstance(value,list): return "\n".join(str(x) for x in value)
    if isinstance(value,dict): return json.dumps(value,ensure_ascii=False)
    return "" if value is None else str(value)
def export_json(doc, out, template_name):
    if Workbook is None: raise RuntimeError("Excel 输出需要 openpyxl")
    cols=template(template_name).get("columns",[]); wb=Workbook(); ws=wb.active; ws.title="Test Cases"
    for col, definition in enumerate(cols,1):
        cell=ws.cell(1,col,definition["label"]); cell.font=Font(bold=True,color="FFFFFF"); cell.fill=PatternFill("solid",fgColor="4F81BD")
    for row, case in enumerate(doc.get("testcases",[]),2):
        for col, definition in enumerate(cols,1):
            cell=ws.cell(row,col,text(case.get(definition["key"],""))); cell.alignment=Alignment(wrap_text=True,vertical="top")
    ws.freeze_panes="A2"; ws.auto_filter.ref=ws.dimensions
    for col in range(1,len(cols)+1): ws.column_dimensions[get_column_letter(col)].width=min(48,max(14,max([len(str(ws.cell(r,col).value or "")) for r in range(1,min(ws.max_row,30)+1)] or [14])+2))
    wb.save(out)
def import_xlsx(path, template_name):
    if Workbook is None: raise RuntimeError("Excel 输入需要 openpyxl")
    wb=load_workbook(path,read_only=True,data_only=True); ws=wb.active; rows=list(ws.iter_rows(values_only=True)); cols=template(template_name).get("columns",[]); out=[]
    for values in rows[1:]:
        raw={d["key"]:(values[i] if i<len(values) else "") for i,d in enumerate(cols)}
        for key in ("preconditions","actions","assertions","source_refs","tags","notes"):
            if key in raw: raw[key]=[x for x in str(raw[key] or "").splitlines() if x.strip()]
        out.append(raw)
    return {"schema_version":"1.0","project":"","source":{"kind":"xlsx","files":[str(path)]},"assumptions":[],"testcases":out}
def main(argv=None):
    ap=argparse.ArgumentParser(); s=ap.add_subparsers(dest="cmd",required=True); e=s.add_parser("export"); e.add_argument("--input",required=True); e.add_argument("--output",required=True); e.add_argument("--template",default="default"); i=s.add_parser("import"); i.add_argument("--input",required=True); i.add_argument("--output",required=True); i.add_argument("--template",default="default"); args=ap.parse_args(argv)
    if args.cmd=="export": export_json(read_doc(args.input),args.output,args.template)
    else: Path(args.output).write_text(json.dumps(import_xlsx(args.input,args.template),ensure_ascii=False,indent=2),encoding="utf-8")
if __name__=="__main__": main()
