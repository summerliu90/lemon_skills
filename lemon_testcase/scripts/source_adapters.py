#!/usr/bin/env python3
"""Input adapters for text, docx, pdf, images, URLs and Postman collections."""
from __future__ import annotations
import argparse, csv, json, re, sys
from pathlib import Path
from typing import Any

def _split(value: Any) -> list[str]:
    if value is None: return []
    if isinstance(value,list): return [str(x).strip() for x in value if str(x).strip()]
    return [x.strip() for x in re.split(r"\r?\n|<br\s*/?>",str(value)) if x.strip()]

def _case(raw: dict[str,Any], index: int, source: str, kind: str="functional") -> dict[str,Any]:
    aliases={"用例编号":"case_id","用例名称":"name","用例标题":"name","模块":"area","所属模块":"area","测试类型":"kind","优先级":"priority","前置条件":"preconditions","前置操作":"preconditions","测试步骤":"actions","执行步骤":"actions","预期结果":"assertions","测试数据":"data","需求依据":"source_refs"}
    d={aliases.get(str(k).strip(),str(k).strip().lower().replace(" ","_")):v for k,v in raw.items()}
    return {"case_id":str(d.get("case_id") or f"LM-IMP-{index:04d}"),"name":str(d.get("name") or "导入测试场景"),"area":str(d.get("area") or "未分类"),"kind":str(d.get("kind") or kind),"priority":str(d.get("priority") or "P2"),"preconditions":_split(d.get("preconditions")),"actions":_split(d.get("actions")),"assertions":_split(d.get("assertions")),"data":d.get("data") or {},"source_refs":_split(d.get("source_refs")) or [source],"tags":_split(d.get("tags")),"notes":_split(d.get("notes")),"automation_candidate":bool(d.get("automation_candidate",False))}

def from_csv(path: str) -> dict[str,Any]:
    with open(path,encoding="utf-8-sig",newline="") as f: rows=list(csv.DictReader(f))
    return _document([_case(row,i,path) for i,row in enumerate(rows,1)],"imported")

def from_markdown(path: str) -> dict[str,Any]:
    text=Path(path).read_text(encoding="utf-8-sig"); rows=[]
    for line in text.splitlines():
        if "|" in line and line.strip(): rows.append([x.strip().replace("\\|","|") for x in line.strip().strip("|").split("|")])
    cases=[]
    if len(rows)>=2:
        headers=rows[0]
        for i,row in enumerate(rows[2:],1):
            if len(row)>=len(headers): cases.append(_case(dict(zip(headers,row)),i,path))
    if not cases:
        section="文档需求"
        for i,line in enumerate(text.splitlines(),1):
            value=line.strip().lstrip("# ").strip()
            if not value: continue
            if line.lstrip().startswith("#"):
                section=value
                continue
            if re.search(r"需求|验收|功能|场景|异常|性能|测试|检查|目标",value):
                cases.append(_case({"name":value,"area":section,"actions":["按照该段落和上下文执行"],"assertions":["满足文档中声明的可观察要求"],"notes":["由文本段落提取，需人工补充精确步骤和断言"]},len(cases)+1,f"{path}#line-{i}","performance" if re.search(r"性能|并发|P95|吞吐|负载",value) else "ui" if re.search(r"界面|页面|布局|按钮|输入框|可访问",value) else "functional"))
    return _document(cases,"markdown")

def from_docx(path: str) -> dict[str,Any]:
    try:
        from docx import Document
    except ImportError: raise RuntimeError("DOCX 解析需要安装 python-docx")
    doc=Document(path); paragraphs=[p.text.strip() for p in doc.paragraphs if p.text.strip()]; cases=[]
    for i,text in enumerate(paragraphs,1):
        if re.match(r"(?:需求|功能|场景|验收)",text):
            cases.append(_case({"name":text,"area":"文档需求","actions":["按照需求执行"],"assertions":["满足文档中的验收标准"]},i,f"{path}#paragraph-{i}"))
    for ti,table in enumerate(doc.tables,1):
        rows=[[cell.text.strip() for cell in row.cells] for row in table.rows]
        if len(rows)>1:
            headers=rows[0]
            for ri,row in enumerate(rows[1:],1):
                cases.append(_case(dict(zip(headers,row)),len(cases)+1,f"{path}#table-{ti}-row-{ri}"))
    return _document(cases,"docx")

def from_pdf(path: str) -> dict[str,Any]:
    try:
        import pdfplumber
    except ImportError: raise RuntimeError("PDF 解析需要安装 pdfplumber")
    cases=[]
    with pdfplumber.open(path) as pdf:
        for page_no,page in enumerate(pdf.pages,1):
            text=page.extract_text() or ""
            for i,line in enumerate((x for x in text.splitlines() if x.strip()),1):
                if re.search(r"需求|功能|验收|场景",line): cases.append(_case({"name":line,"area":"PDF需求","actions":["按照页面需求执行"],"assertions":["满足原文验收条件"]},len(cases)+1,f"{path}#page-{page_no}-line-{i}"))
    return _document(cases,"pdf")

def from_image(path: str, ocr_text: str="") -> dict[str,Any]:
    notes=["图像内容需要人工确认；本适配器不臆测不可见交互"]
    if ocr_text: notes.append("OCR 文本由调用方提供")
    return _document([_case({"name":"设计稿页面测试清单","area":"UI页面","kind":"ui","actions":["检查页面布局和交互组件","检查加载、空、错误和禁用状态"],"assertions":["页面元素与设计稿一致","交互反馈和可访问性满足要求"],"notes":notes,"source_refs":[path]},1,path,"ui")],"image")

def from_url_text(url: str, text: str) -> dict[str,Any]:
    cases=[]
    for i,line in enumerate((x for x in text.splitlines() if x.strip()),1):
        if re.search(r"需求|验收|功能|场景",line): cases.append(_case({"name":line,"area":"在线文档","actions":["按在线文档要求执行"],"assertions":["满足在线文档验收要求"]},i,url))
    return _document(cases,"online")

def from_postman(path: str) -> dict[str,Any]:
    obj=json.loads(Path(path).read_text(encoding="utf-8-sig")); cases=[]; number=1
    def walk(items, folder=""):
        nonlocal number
        for item in items or []:
            if item.get("item"): walk(item["item"],item.get("name",folder)); continue
            req=item.get("request",{}); url=req.get("url",""); url=url.get("raw","") if isinstance(url,dict) else url; method=req.get("method","GET"); assertions=[]
            for event in item.get("event",[]):
                script=event.get("script",{}).get("exec",[]); assertions.extend([str(x) for x in script if "expect" in str(x) or "status" in str(x)])
            cases.append(_case({"name":item.get("name") or f"{method} {url}","area":folder or "API","kind":"api","method":method,"path":url,"actions":[f"发送 {method} 请求到 {url}"],"assertions":assertions or ["响应满足接口契约"],"data":{"headers":req.get("header",[]),"body":req.get("body",{})},"source_refs":[f"{path}#{item.get('name','request')}"]},number,path,"api")); number+=1
    walk(obj.get("item",[])); return _document(cases,"postman")

def _document(cases, source_kind): return {"schema_version":"1.0","project":"","source":{"kind":source_kind},"assumptions":[],"testcases":cases}

def main(argv=None):
    ap=argparse.ArgumentParser(); ap.add_argument("--input",required=True); ap.add_argument("--output",required=True); ap.add_argument("--ocr-text"); args=ap.parse_args(argv); p=Path(args.input); ext=p.suffix.lower()
    if ext==".csv": doc=from_csv(args.input)
    elif ext in (".md",".markdown",".txt"): doc=from_markdown(args.input)
    elif ext==".docx": doc=from_docx(args.input)
    elif ext==".pdf": doc=from_pdf(args.input)
    elif ext in (".png",".jpg",".jpeg",".webp"): doc=from_image(args.input,args.ocr_text or "")
    elif ext==".json":
        obj=json.loads(p.read_text(encoding="utf-8-sig"))
        if "item" in obj and "info" in obj:
            doc=from_postman(args.input)
        elif "paths" in obj and ("openapi" in obj or "swagger" in obj):
            sys.path.insert(0,str(Path(__file__).resolve().parent))
            from openapi_cases import generate
            doc=generate(obj,["valid","missing","empty","wrong_type"])
        else: doc=obj
    else: raise SystemExit(f"不支持的输入类型: {ext}")
    Path(args.output).write_text(json.dumps(doc,ensure_ascii=False,indent=2),encoding="utf-8"); print(f"adapted {len(doc.get('testcases',[]))} cases")
if __name__=="__main__": sys.exit(main())
