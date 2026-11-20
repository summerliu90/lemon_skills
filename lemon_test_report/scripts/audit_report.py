#!/usr/bin/env python3
"""审计测试报告中的指标一致性、门禁证据和常见敏感信息。"""
from __future__ import annotations
import argparse, json, re, sys
from pathlib import Path

NUM = r"(\d+(?:\.\d+)?)"

def first(pattern, text, cast=float):
    m = re.search(pattern, text, re.I | re.M)
    return cast(m.group(1)) if m else None

def scan_secrets(text):
    checks = {
        "email": r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
        "phone": r"(?<!\d)1[3-9]\d{9}(?!\d)",
        "bearer": r"(?i)\bBearer\s+[A-Za-z0-9._-]{12,}",
        "token_assignment": r"(?i)\b(?:token|api[_-]?key|secret)\s*[:=]\s*[^\s`]{8,}",
        "private_ip": r"\b(?:10\.\d{1,3}\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3})\b",
    }
    hits = []
    for kind, pattern in checks.items():
        for m in re.finditer(pattern, text):
            line = text.count("\n", 0, m.start()) + 1
            hits.append({"type": kind, "line": line, "preview": f"<redacted:{kind}>"})
    return hits

def audit(text, policy):
    warnings, errors = [], []
    cases = {}
    labels = {"total":"总(?:用例|执行)(?:数)?", "passed":"通过", "failed":"失败", "blocked":"阻塞", "skipped":"跳过", "not_run":"未执行"}
    for key, label in labels.items():
        value = first(rf"{label}\s*[:：]?\s*(\d+)", text, int)
        if value is not None: cases[key] = value
    pass_rate = first(rf"通过率\s*[:：]?\s*{NUM}\s*%", text)
    close_rate = first(rf"(?:关闭率|缺陷关闭率)\s*[:：]?\s*{NUM}\s*%", text)
    bugs = first(r"(?:Bug|缺陷)\s*(?:总数|总计|统计)\s*[:：]?\s*(\d+)", text, int)
    p0 = first(r"P0\s*[:：]?\s*(\d+)", text, int)
    p1 = first(r"P1\s*[:：]?\s*(\d+)", text, int)
    if pass_rate is not None and not 0 <= pass_rate <= 100: errors.append("通过率超出 0-100 范围")
    if close_rate is not None and not 0 <= close_rate <= 100: errors.append("关闭率超出 0-100 范围")
    if cases and all(k in cases for k in ("passed","failed","blocked","skipped")):
        base = sum(cases[k] for k in ("passed","failed","blocked","skipped"))
        if cases.get("total") is not None and base != cases["total"]:
            errors.append(f"用例总数与状态合计不一致：总数 {cases['total']}，状态合计 {base}")
        calculated = round(cases["passed"] / base * 100, 2) if base else None
        if calculated is not None and pass_rate is not None and abs(calculated - pass_rate) > 0.11:
            errors.append(f"通过率与计数冲突：计算值 {calculated}%，报告值 {pass_rate}%")
    if bugs == 0 and close_rate is not None:
        warnings.append("缺陷总数为 0 时关闭率应显示 N/A，而不是百分比")
    gates = {
        "pass_rate": pass_rate,
        "pass_rate_min": policy.get("pass_rate_min"),
        "p0": p0,
        "p0_max": policy.get("p0_max"),
        "p1": p1,
        "p1_max": policy.get("p1_max"),
    }
    gate_failures = []
    if pass_rate is None: gate_failures.append("缺少通过率证据")
    elif policy.get("pass_rate_min") is not None and pass_rate < policy["pass_rate_min"]: gate_failures.append("通过率未达到门槛")
    if p0 is None: gate_failures.append("缺少 P0 证据")
    elif policy.get("p0_max") is not None and p0 > policy["p0_max"]: gate_failures.append("P0 数量超过门槛")
    if p1 is None: gate_failures.append("缺少 P1 证据")
    elif policy.get("p1_max") is not None and p1 > policy["p1_max"]: gate_failures.append("P1 数量超过门槛")
    secrets = scan_secrets(text)
    if secrets: warnings.append(f"发现 {len(secrets)} 处疑似敏感信息，渲染前应脱敏")
    missing_evidence = {"缺少通过率证据", "缺少 P0 证据", "缺少 P1 证据"}
    hard_gate_failures = [item for item in gate_failures if item not in missing_evidence]
    conclusion = "No-Go" if errors or hard_gate_failures else ("Pending" if gate_failures else "Go")
    return {"schema":"lemon-test-report/audit-v1", "metrics":{"cases":cases,"pass_rate":pass_rate,"close_rate":close_rate,"bugs":bugs,"p0":p0,"p1":p1}, "gates":gates, "gate_failures":gate_failures, "errors":errors, "warnings":warnings, "sensitive_hits":secrets, "conclusion":conclusion}

def main():
    ap = argparse.ArgumentParser(description="审计测试报告并输出机器可读结果")
    ap.add_argument("report", type=Path); ap.add_argument("--policy", type=Path)
    ap.add_argument("--json", dest="json_path", type=Path)
    args = ap.parse_args(); text = args.report.read_text(encoding="utf-8")
    policy = json.loads(args.policy.read_text(encoding="utf-8")) if args.policy else {}
    result = audit(text, policy)
    payload = json.dumps(result, ensure_ascii=False, indent=2)
    if args.json_path: args.json_path.write_text(payload + "\n", encoding="utf-8")
    print(payload)
    return 2 if result["errors"] or result["gate_failures"] else 0
if __name__ == "__main__": sys.exit(main())
