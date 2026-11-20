#!/usr/bin/env python3
"""Additional renderers: nested JSON, HTML review sheet and plain text export."""
from __future__ import annotations
import argparse,html,json,sys
from pathlib import Path
from lemon_cases import load,scalar,read_template
def render_jsonl(doc): return "".join(json.dumps(c,ensure_ascii=False)+"\n" for c in doc.get("testcases",[]))
def render_text(doc):
    out=[doc.get("project") or "测试用例", "="*40]
    for c in doc.get("testcases",[]):
        out += [f"[{c.get('case_id')}] {c.get('name')}",f"模块: {c.get('area')} | 类型: {c.get('kind')} | 优先级: {c.get('priority')}","前置:"]+[f"  - {x}" for x in c.get("preconditions",[])]+["步骤:"]+[f"  {i}. {x}" for i,x in enumerate(c.get("actions",[]),1)]+["预期:"]+[f"  - {x}" for x in c.get("assertions",[])]+[""]
    return "\n".join(out)
def render_html(doc):
    rows=[]
    for c in doc.get("testcases",[]):
        rows.append("<tr>"+"".join(f"<td>{html.escape(scalar(c.get(k,'')))}</td>" for k in ("case_id","name","area","kind","priority","actions","assertions"))+"</tr>")
    return "<!doctype html><meta charset='utf-8'><title>测试用例审核</title><style>body{font-family:system-ui}table{border-collapse:collapse;width:100%}td,th{border:1px solid #bbb;padding:6px;vertical-align:top;white-space:pre-wrap}th{background:#eef}</style><table><tr><th>ID</th><th>名称</th><th>模块</th><th>类型</th><th>优先级</th><th>步骤</th><th>预期</th></tr>"+"".join(rows)+"</table>"
def render_schema(doc,template):
    cols=read_template(template); return {"schema_version":"1.0","template":template,"columns":[x["key"] for x in cols],"rows":[{x["key"]:c.get(x["key"],"") for x in cols} for c in doc.get("testcases",[])]}
def main(argv=None):
    ap=argparse.ArgumentParser(); ap.add_argument("--input",required=True); ap.add_argument("--output",required=True); ap.add_argument("--format",choices=["jsonl","text","html","schema"],required=True); ap.add_argument("--template",default="default"); args=ap.parse_args(argv); doc=load(args.input)
    result=render_jsonl(doc) if args.format=="jsonl" else render_text(doc) if args.format=="text" else render_html(doc) if args.format=="html" else json.dumps(render_schema(doc,args.template),ensure_ascii=False,indent=2)
    Path(args.output).write_text(result,encoding="utf-8"); print(f"rendered {len(doc.get('testcases',[]))} cases -> {args.output}")
if __name__=="__main__": sys.exit(main())
