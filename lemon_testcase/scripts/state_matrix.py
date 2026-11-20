#!/usr/bin/env python3
"""Turn a simple state graph into transition test cases."""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
def read(path): return json.loads(Path(path).read_text(encoding="utf-8-sig"))
def build(graph):
    cases=[]; transitions=graph.get("transitions",[])
    for index,item in enumerate(transitions,1):
        source=item.get("from","未知状态"); target=item.get("to","未知状态"); event=item.get("event","执行状态变更"); allowed=item.get("allowed",True); name=f"{source} -> {target} - {event}"
        cases.append({"case_id":f"LM-STATE-{index:04d}","name":name,"area":graph.get("area","状态流程"),"kind":"functional","priority":"P1" if allowed else "P2","preconditions":[f"当前状态为 {source}"],"actions":[f"触发事件：{event}"],"assertions":[f"状态变为 {target}" if allowed else "状态保持在当前状态并给出拒绝反馈"],"data":{"from":source,"to":target,"event":event},"source_refs":graph.get("source_refs",[]),"tags":["state","positive" if allowed else "negative"],"notes":[] if allowed else ["该迁移被标记为禁止，需确认错误反馈"],"automation_candidate":True})
    return {"schema_version":"1.0","project":graph.get("project",""),"source":{"kind":"state-graph"},"assumptions":[],"testcases":cases}
def main(argv=None):
    ap=argparse.ArgumentParser(); ap.add_argument("--input",required=True); ap.add_argument("--output",required=True); args=ap.parse_args(argv); Path(args.output).write_text(json.dumps(build(read(args.input)),ensure_ascii=False,indent=2),encoding="utf-8"); print("state cases generated")
if __name__=="__main__": sys.exit(main())
