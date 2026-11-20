#!/usr/bin/env python3
"""Coverage and consistency audit for canonical Lemon testcase documents.

This module intentionally reports explainable findings instead of inventing a
coverage percentage.  A requirement can be mapped to cases with --requirements
using a simple JSON array of requirement identifiers and text.
"""
from __future__ import annotations
import argparse, json, re, sys
from pathlib import Path
from collections import Counter, defaultdict
from typing import Any

SEVERITY = {"error": 3, "warning": 2, "info": 1}
RISK_TAGS = {"auth", "permission", "security", "payment", "boundary", "negative", "state", "concurrency"}

def read_doc(path: str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))

def issue(level: str, code: str, text: str, case_id: str = "") -> dict[str, str]:
    return {"level": level, "code": code, "case_id": case_id, "message": text}

def inspect_structure(doc: dict[str, Any]) -> list[dict[str, str]]:
    found=[]; cases=doc.get("testcases", [])
    if not isinstance(cases, list): return [issue("error", "ROOT_CASES", "testcases 不是数组")]
    seen=set()
    for index, case in enumerate(cases, 1):
        cid=str(case.get("case_id", ""))
        if cid in seen: found.append(issue("error", "DUPLICATE_ID", "用例编号重复", cid))
        seen.add(cid)
        for field in ("case_id", "name", "area", "kind", "priority", "preconditions", "actions", "assertions"):
            if field not in case or case[field] in ("", [], None): found.append(issue("error", "REQUIRED_FIELD", f"缺少字段 {field}", cid or str(index)))
        if case.get("priority") not in ("P0", "P1", "P2", "P3"): found.append(issue("error", "BAD_PRIORITY", "优先级不在 P0-P3", cid))
        for field in ("preconditions", "actions", "assertions", "source_refs", "tags", "notes"):
            if field in case and not isinstance(case[field], list): found.append(issue("error", "BAD_LIST", f"字段 {field} 不是数组", cid))
        if not case.get("source_refs"): found.append(issue("warning", "NO_SOURCE", "缺少需求依据，无法回溯生成原因", cid))
        if len(case.get("assertions", [])) == 1 and re.search(r"报错|成功|正常", case["assertions"][0]) and not re.search(r"状态|提示|返回|显示|数据|字段|跳转", case["assertions"][0]):
            found.append(issue("warning", "VAGUE_ASSERTION", "预期结果可能不可观察", cid))
        if "negative" in case.get("tags", []) and not any(re.search(r"拒绝|错误|失败|不应|禁止|状态码", x) for x in case.get("assertions", [])):
            found.append(issue("warning", "WEAK_NEGATIVE", "负向案例没有明确拒绝或错误断言", cid))
    return found

def inventory(doc: dict[str, Any]) -> dict[str, Any]:
    cases=doc.get("testcases", []); by_area=Counter(x.get("area", "") for x in cases); by_kind=Counter(x.get("kind", "") for x in cases); by_priority=Counter(x.get("priority", "") for x in cases); tags=Counter(t for x in cases for t in x.get("tags", []))
    return {"total":len(cases), "areas":dict(by_area), "kinds":dict(by_kind), "priorities":dict(by_priority), "tags":dict(tags), "with_sources":sum(bool(x.get("source_refs")) for x in cases), "automation_candidates":sum(bool(x.get("automation_candidate")) for x in cases)}

def compare_requirements(doc: dict[str, Any], req_path: str | None) -> list[dict[str, str]]:
    if not req_path: return []
    requirements=json.loads(Path(req_path).read_text(encoding="utf-8")); cases=doc.get("testcases", []); out=[]
    for req in requirements:
        rid=str(req.get("id", "")); text=str(req.get("text", "")); hits=[]
        for c in cases:
            hay=" ".join([str(c.get("name", "")), *c.get("source_refs", []), *c.get("notes", [])])
            if rid and rid in hay or (text and any(word in hay for word in re.findall(r"[\w\u4e00-\u9fff]{2,}", text)[:4])): hits.append(c.get("case_id", ""))
        if not hits: out.append(issue("warning", "UNCOVERED_REQUIREMENT", f"没有找到需求 {rid} 的案例映射", rid))
    return out

def risk_gaps(doc: dict[str, Any]) -> list[dict[str, str]]:
    cases=doc.get("testcases", []); out=[]; areas=defaultdict(list)
    for c in cases: areas[c.get("area", "")].append(c)
    for area, values in areas.items():
        tags={t for c in values for t in c.get("tags", [])}; negative=any("negative" in c.get("tags", []) for c in values); positive=any("positive" in c.get("tags", []) for c in values)
        if not positive: out.append(issue("warning", "NO_POSITIVE", f"模块 {area} 没有正向案例", area))
        if not negative: out.append(issue("warning", "NO_NEGATIVE", f"模块 {area} 没有负向案例", area))
        if any(c.get("priority") == "P0" for c in values) and "boundary" not in tags: out.append(issue("info", "NO_BOUNDARY", f"核心模块 {area} 尚未标记边界案例", area))
    return out

def main(argv=None):
    ap=argparse.ArgumentParser(); ap.add_argument("--input",required=True); ap.add_argument("--requirements"); ap.add_argument("--json",action="store_true"); args=ap.parse_args(argv)
    doc=read_doc(args.input); findings=inspect_structure(doc)+compare_requirements(doc,args.requirements)+risk_gaps(doc); result={"inventory":inventory(doc),"findings":findings,"valid":not any(x["level"]=="error" for x in findings)}
    print(json.dumps(result,ensure_ascii=False,indent=2) if args.json else f"案例 {result['inventory']['total']} 条，问题 {len(findings)} 条，结构有效={result['valid']}")
    if any(x["level"]=="error" for x in findings): return 1
    return 0
if __name__=="__main__": sys.exit(main())
