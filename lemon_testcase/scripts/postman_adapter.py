#!/usr/bin/env python3
"""Postman v2 collection adapter with variables, auth and response examples."""
from __future__ import annotations
import argparse,json,re,sys
from pathlib import Path
def load(path): return json.loads(Path(path).read_text(encoding="utf-8-sig"))
def variable_map(obj):
    return {str(x.get("key")):x.get("value","") for x in obj.get("variable",[]) if isinstance(x,dict)}
def resolve(value,variables):
    return re.sub(r"\{\{([^}]+)\}\}",lambda m:str(variables.get(m.group(1),m.group(0))),str(value))
def headers(value,variables):
    result={}
    for item in value or []:
        if isinstance(item,dict) and not item.get("disabled"): result[str(item.get("key"))]=resolve(item.get("value",""),variables)
    return result
def body(req,variables):
    b=req.get("body",{}) or {}; mode=b.get("mode")
    if mode=="raw":
        raw=resolve(b.get("raw",""),variables)
        try: return json.loads(raw)
        except Exception: return raw
    if mode in ("urlencoded","formdata"):
        return {str(x.get("key")):resolve(x.get("value",""),variables) for x in b.get(mode,[]) if not x.get("disabled")}
    return b
def script_assertions(item):
    assertions=[]
    for event in item.get("event",[]):
        script=event.get("script",{}) or {}
        code="\n".join(map(str,script.get("exec",[])))
        for m in re.finditer(r"(?:response|pm\.response)\.(?:to\.have\.status|status).*?(\d{3})",code,re.I): assertions.append(f"状态码为 {m.group(1)}")
        for m in re.finditer(r"expect\([^)]*\)\.to\.(?:have\.)?(?:property|equal|eql)\s*\(?['\"]([^'\"]+)",code,re.I): assertions.append(f"响应包含断言字段 {m.group(1)}")
        if "responseTime" in code: assertions.append("响应时间满足脚本中声明的目标")
    return assertions
def response_statuses(item):
    values=[]
    for response in item.get("response",[]) or []:
        if isinstance(response,dict):
            code=response.get("code")
            if str(code).isdigit(): values.append(int(code))
    return values
def convert(path):
    obj=load(path); variables=variable_map(obj); cases=[]; number=1
    def walk(items,folder=""):
        nonlocal number
        for item in items or []:
            if item.get("item"):
                walk(item["item"],item.get("name") or folder); continue
            req=item.get("request",{}) or {}; url=req.get("url","")
            if isinstance(url,dict): url=url.get("raw") or "/".join(map(str,url.get("path",[])))
            url=resolve(url,variables); method=str(req.get("method","GET")).upper(); assertions=script_assertions(item); statuses=response_statuses(item)
            cases.append({"case_id":f"LM-POSTMAN-{number:04d}","name":item.get("name") or f"{method} {url}","area":folder or "API","kind":"api","priority":"P1","preconditions":["Postman 变量和环境已准备"],"actions":[f"发送 {method} {url} 请求","检查请求头、认证和请求数据"],"assertions":assertions or ["响应状态和结构符合接口约定"],"data":{"headers":headers(req.get("header"),variables),"body":body(req,variables),"auth":req.get("auth",{})},"source_refs":[f"{path}#{item.get('name','request')}"],"tags":["postman","api"],"notes":[],"automation_candidate":True,"method":method,"path":url,"expected_status":statuses}); number+=1
    walk(obj.get("item",[])); return {"schema_version":"1.0","project":obj.get("info",{}).get("name","Postman collection"),"source":{"kind":"postman","files":[path]},"assumptions":[],"testcases":cases}
def main(argv=None):
    ap=argparse.ArgumentParser(); ap.add_argument("--input",required=True); ap.add_argument("--output",required=True); args=ap.parse_args(argv); doc=convert(args.input); Path(args.output).write_text(json.dumps(doc,ensure_ascii=False,indent=2),encoding="utf-8"); print(f"converted {len(doc['testcases'])} Postman requests")
if __name__=="__main__": sys.exit(main())
