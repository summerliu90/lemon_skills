#!/usr/bin/env python3
"""Apply externalized Lemon quality standards to canonical case JSON."""
from __future__ import annotations
import argparse, json, re, sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RULE_DIR = ROOT / "assets" / "rules"

def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))

def load_rules(rule_dir: Path = RULE_DIR) -> dict[str, dict[str, Any]]:
    rules = {}
    for path in sorted(rule_dir.glob("*.json")):
        item = read_json(path)
        if item.get("kind"):
            rules[item["kind"]] = item
    return rules

def finding(level: str, code: str, message: str, path: str, hint: str = "") -> dict[str, str]:
    return {"level": level, "code": code, "path": path, "message": message, "hint": hint}

def text_of(value: Any) -> str:
    if isinstance(value, list):
        return " ".join(text_of(x) for x in value)
    if isinstance(value, dict):
        return " ".join(text_of(v) for v in value.values())
    return "" if value is None else str(value)

def validate_sources(doc: dict[str, Any], findings: list[dict[str, str]]) -> None:
    sources = doc.get("sources", [])
    if not sources and doc.get("source"):
        legacy = doc["source"]
        source_id = legacy.get("source_id") if isinstance(legacy, dict) else None
        if source_id:
            sources = [legacy]
        else:
            return
    if not isinstance(sources, list):
        findings.append(finding("error", "SOURCES_TYPE", "sources 必须是数组", "sources"))
        return
    known = {str(s.get("source_id")) for s in sources if isinstance(s, dict)}
    for i, source in enumerate(sources):
        path = f"sources[{i}]"
        if not isinstance(source, dict):
            findings.append(finding("error", "SOURCE_OBJECT", "来源项必须是对象", path))
            continue
        for field in ("source_id", "source_type", "locator"):
            if not source.get(field):
                findings.append(finding("error", "SOURCE_FIELD", f"来源缺少 {field}", path))
    for i, case in enumerate(doc.get("testcases", [])):
        refs = case.get("source_refs", []) if isinstance(case, dict) else []
        for ref in refs if isinstance(refs, list) else []:
            base = str(ref).split("#", 1)[0]
            if base not in known and str(ref) not in known:
                findings.append(finding("warning", "ORPHAN_SOURCE", f"找不到来源引用 {ref}", f"testcases[{i}].source_refs"))

def validate_case(case: dict[str, Any], index: int, rules: dict[str, dict[str, Any]], findings: list[dict[str, str]]) -> None:
    kind = case.get("kind")
    rule = rules.get(kind)
    path = f"testcases[{index}]"
    if not rule:
        findings.append(finding("warning", "NO_KIND_RULE", f"没有 {kind} 的标准规则", path))
        return
    for field in rule.get("required_case_fields", []):
        if case.get(field) in (None, "", []):
            findings.append(finding("error", "STANDARD_REQUIRED", f"{rule.get('label', kind)}缺少必填字段 {field}", f"{path}.{field}"))
    tags = {str(x).lower() for x in case.get("tags", [])}
    allowed = {str(x).lower() for x in rule.get("required_tags_any", [])}
    if allowed and not tags.intersection(allowed):
        hint = "至少选择一个: " + ", ".join(sorted(allowed))
        findings.append(finding("warning", "COVERAGE_TAG", f"缺少 {rule.get('label', kind)} 覆盖标签", f"{path}.tags", hint))
    action_text = text_of(case.get("actions"))
    assertion_text = text_of(case.get("assertions"))
    if len(action_text.strip()) < 8:
        findings.append(finding("warning", "THIN_ACTION", "步骤过短，可能无法执行", f"{path}.actions"))
    patterns = rule.get("assertion_patterns", [])
    if assertion_text.strip() and patterns and not any(re.search(re.escape(p), assertion_text, re.I) for p in patterns):
        findings.append(finding("warning", "WEAK_ASSERTION", "预期未体现可观察结果或该类型关键指标", f"{path}.assertions"))
    if kind == "api":
        methods = {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS", "TRACE"}
        if str(case.get("method", "")).upper() not in methods:
            findings.append(finding("error", "API_METHOD", "method 不是有效 HTTP 方法", f"{path}.method"))
        if not str(case.get("path", "")).startswith("/"):
            findings.append(finding("warning", "API_PATH", "接口 path 最好以 / 开始", f"{path}.path"))
    if kind == "automation" and not isinstance(case.get("automation_candidate"), bool):
        findings.append(finding("error", "AUTOMATION_FLAG", "automation_candidate 必须是布尔值", f"{path}.automation_candidate"))

def summarize(findings: list[dict[str, str]]) -> dict[str, Any]:
    counts = {level: sum(1 for item in findings if item["level"] == level) for level in ("error", "warning", "info")}
    return {"valid": counts["error"] == 0, "counts": counts, "findings": findings}

def validate(doc: Any, rule_dir: Path = RULE_DIR) -> dict[str, Any]:
    findings: list[dict[str, str]] = []
    rules = load_rules(rule_dir)
    if not isinstance(doc, dict):
        return summarize([finding("error", "ROOT_TYPE", "输入必须是 JSON 对象", "")])
    for field in rules.get("output", {}).get("required_document_fields", []):
        if field not in doc or doc[field] in (None, ""):
            findings.append(finding("error", "DOCUMENT_REQUIRED", f"文档缺少 {field}", field))
    cases = doc.get("testcases")
    if not isinstance(cases, list):
        findings.append(finding("error", "CASES_TYPE", "testcases 必须是数组", "testcases"))
        return summarize(findings)
    validate_sources(doc, findings)
    ids: set[str] = set()
    for i, case in enumerate(cases):
        if not isinstance(case, dict):
            findings.append(finding("error", "CASE_TYPE", "案例必须是对象", f"testcases[{i}]"))
            continue
        cid = str(case.get("case_id", ""))
        if not cid:
            findings.append(finding("error", "CASE_ID", "案例编号不能为空", f"testcases[{i}].case_id"))
        elif cid in ids:
            findings.append(finding("error", "DUPLICATE_ID", f"案例编号重复: {cid}", f"testcases[{i}].case_id"))
        ids.add(cid)
        validate_case(case, i, rules, findings)
    return summarize(findings)

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate canonical cases with Lemon standards")
    parser.add_argument("--input", required=True)
    parser.add_argument("--rules", type=Path, default=RULE_DIR)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    result = validate(read_json(Path(args.input)), args.rules)
    payload = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)
    return 0 if result["valid"] else 1

if __name__ == "__main__":
    sys.exit(main())
