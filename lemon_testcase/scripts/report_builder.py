#!/usr/bin/env python3
"""Create a compact human-readable audit report from canonical cases."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
from collections import Counter
def load(path): return json.loads(Path(path).read_text(encoding="utf-8-sig"))
def report(doc):
    cases=doc.get("testcases",[]); by_area=Counter(c.get("area","") for c in cases); by_kind=Counter(c.get("kind","") for c in cases); by_priority=Counter(c.get("priority","") for c in cases); tags=Counter(t for c in cases for t in c.get("tags",[]));
    lines=[f"# {doc.get('project') or '测试用例'}审核报告","",f"总用例数：{len(cases)}","", "## 模块分布",""]
    lines.extend([f"- {key}: {value}" for key,value in by_area.items()]); lines += ["","## 测试类型",""]; lines.extend([f"- {key}: {value}" for key,value in by_kind.items()]); lines += ["","## 优先级",""]; lines.extend([f"- {key}: {value}" for key,value in sorted(by_priority.items())]); lines += ["","## 标签",""]; lines.extend([f"- {key}: {value}" for key,value in sorted(tags.items())]); lines += ["","## 人工确认",""]
    notes=sorted({n for c in cases for n in c.get("notes",[])})
    lines.extend([f"- {note}" for note in notes] or ["- 未记录待确认项"]); return "\n".join(lines)+"\n"
def main(argv=None):
    ap=argparse.ArgumentParser(); ap.add_argument("--input",required=True); ap.add_argument("--output",required=True); args=ap.parse_args(argv); Path(args.output).write_text(report(load(args.input)),encoding="utf-8"); print(f"report -> {args.output}")
if __name__=="__main__": sys.exit(main())
