#!/usr/bin/env python3
"""Build cross-feature scenarios from canonical cases and dependency hints."""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
from collections import defaultdict
def load(path): return json.loads(Path(path).read_text(encoding="utf-8-sig"))
def save(obj,path): Path(path).write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding="utf-8")
def endpoint_key(case): return f"{case.get('method','')} {case.get('path','')}".strip()
def plan(doc):
    cases=doc.get("testcases",[]); api=[c for c in cases if c.get("kind")=="api"]; grouped=defaultdict(list)
    for c in api: grouped[c.get("area", "API")].append(c)
    scenarios=[]; number=1
    for area,items in grouped.items():
        if len(items)<2: continue
        ordered=sorted(items,key=lambda x:(str(x.get("method")),str(x.get("path"))))
        steps=[]; refs=[]
        for c in ordered[:5]:
            refs.append(c.get("case_id")); steps.append({"case_id":c.get("case_id"),"action":f"调用 {endpoint_key(c)}","capture":["响应状态","资源 ID 或业务结果"]})
        scenarios.append({"case_id":f"LM-SCENARIO-{number:04d}","name":f"{area}接口串联场景","area":area,"kind":"functional","priority":"P1","preconditions":["依赖接口可访问","准备独立测试数据"],"actions":["按顺序执行依赖接口并传递动态变量",* [x["action"] for x in steps]],"assertions":["每个步骤返回符合契约的结果","前一步输出可被后一步安全使用","最终业务状态与需求一致"],"data":{"steps":steps},"source_refs":refs,"tags":["scenario","dependency"],"notes":["接口依赖顺序由同一模块和可用案例推断，交付前需人工确认"],"automation_candidate":True}); number+=1
    return {"schema_version":"1.0","project":doc.get("project",""),"source":{"kind":"scenario"},"assumptions":[],"testcases":scenarios}
def main(argv=None):
    ap=argparse.ArgumentParser(); ap.add_argument("--input",required=True); ap.add_argument("--output",required=True); args=ap.parse_args(argv); save(plan(load(args.input)),args.output); print(f"planned scenarios -> {args.output}")
if __name__=="__main__": sys.exit(main())
