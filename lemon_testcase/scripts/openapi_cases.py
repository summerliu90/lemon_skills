#!/usr/bin/env python3
"""Generate reviewable API cases from OpenAPI 2/3 JSON or YAML."""
from __future__ import annotations
import argparse, json, re, sys
from pathlib import Path
from typing import Any
try:
    import yaml
except ImportError:
    yaml = None

HTTP = {"get", "post", "put", "patch", "delete", "head", "options", "trace"}

def read_spec(path: str) -> dict[str, Any]:
    text = Path(path).read_text(encoding="utf-8-sig")
    if Path(path).suffix.lower() in (".yaml", ".yml"):
        if yaml is None: raise RuntimeError("读取 YAML 需要 PyYAML；也可先转换为 JSON")
        return yaml.safe_load(text)
    return json.loads(text)

class Resolver:
    def __init__(self, root): self.root, self.cache = root, {}
    def get(self, ref: str) -> Any:
        if not ref.startswith("#/"): return {"$ref": ref}
        cur: Any = self.root
        for part in ref[2:].split("/"): cur = cur.get(part.replace("~1", "/").replace("~0", "~"), {})
        return cur
    def expand(self, value: Any, depth: int = 0) -> Any:
        if depth > 10: return value
        if isinstance(value, dict) and "$ref" in value:
            base = self.expand(self.get(value["$ref"]), depth + 1); extra = {k:v for k,v in value.items() if k != "$ref"}
            return {**base, **{k:self.expand(v, depth + 1) for k,v in extra.items()}} if isinstance(base, dict) else base
        if isinstance(value, dict): return {k:self.expand(v, depth + 1) for k,v in value.items()}
        if isinstance(value, list): return [self.expand(v, depth + 1) for v in value]
        return value

def sample(schema: dict[str, Any], resolver: Resolver, mode: str = "valid") -> Any:
    schema = resolver.expand(schema or {})
    if "example" in schema: return schema["example"]
    if "default" in schema: return schema["default"]
    if schema.get("enum"): return schema["enum"][0] if mode == "valid" else "__invalid_enum__"
    if schema.get("oneOf") or schema.get("anyOf"): return sample((schema.get("oneOf") or schema.get("anyOf"))[0], resolver, mode)
    typ = schema.get("type")
    if typ == "object" or "properties" in schema:
        out = {}
        required = set(schema.get("required", []))
        for name, child in schema.get("properties", {}).items():
            if mode != "missing" or name != next(iter(required), ""): out[name] = sample(child, resolver, mode)
        return out
    if typ == "array": return [sample(schema.get("items", {}), resolver, mode)]
    if typ == "integer" or typ == "number":
        if mode == "below_min" and "minimum" in schema: return schema["minimum"] - 1
        if mode == "above_max" and "maximum" in schema: return schema["maximum"] + 1
        return schema.get("minimum", 1)
    if typ == "boolean": return True
    if typ == "string":
        if mode == "empty": return ""
        if mode == "too_long": return "x" * (int(schema.get("maxLength", 16)) + 1)
        return "sample@example.com" if schema.get("format") == "email" else "sample"
    return None

def constraints(schema: dict[str, Any], resolver: Resolver) -> list[str]:
    s = resolver.expand(schema or {}); out = []
    for name in ("type", "format", "minLength", "maxLength", "minimum", "maximum", "minItems", "maxItems", "pattern"):
        if name in s: out.append(f"{name}={s[name]}")
    if s.get("enum"): out.append("enum=" + ",".join(map(str, s["enum"])))
    return out

def parameter_schema(param: dict[str, Any], resolver: Resolver) -> dict[str, Any]:
    return resolver.expand(param.get("schema", param.get("content", {}).get("application/json", {}).get("schema", {})))

def make_case(api: dict[str, Any], name: str, mode: str, ordinal: int, resolver: Resolver, path: str, method: str) -> dict[str, Any]:
    params = api.get("parameters", []); body = api.get("requestBody", {})
    payload: dict[str, Any] = {}; descriptions = []
    for p in params:
        p = resolver.expand(p); location, pname = p.get("in", "query"), p.get("name", "param")
        schema = parameter_schema(p, resolver); payload[f"{location}.{pname}"] = sample(schema, resolver, mode)
        descriptions.append(f"{location}.{pname}: " + ("; ".join(constraints(schema, resolver)) or "按契约"))
    if body:
        schema = resolver.expand(body.get("content", {}).get("application/json", {}).get("schema", body.get("schema", {})))
        payload["body"] = sample(schema, resolver, mode); descriptions.extend(constraints(schema, resolver))
    responses = api.get("responses", {}); statuses = [int(x) for x in responses if str(x).isdigit()]
    ok = next((x for x in statuses if 200 <= x < 300), statuses[0] if statuses else None)
    negative = mode != "valid"; expected = [x for x in statuses if x >= 400] if negative else ([ok] if ok else [])
    if not expected: expected = [400] if negative else []
    method_label = {"valid":"正常流程", "missing":"非法输入", "empty":"非法输入", "wrong_type":"非法输入", "below_min":"边界值", "above_max":"边界值", "too_long":"边界值", "boundary":"边界值", "auth":"非法输入", "negative":"非法输入"}.get(mode, mode)
    source = [f"{method.upper()} {path}"] + descriptions
    area = api.get("tags", [path.split('/')[1] if '/' in path else "API"])[0]
    prefix = "DL" if any(x in (str(api.get("summary")) + path).lower() for x in ("登录", "login", "auth")) else "".join(x for x in str(area).upper() if x.isalnum())[:2] or "API"
    flow_type = "正常流程" if mode == "valid" or method_label == "边界值" else "异常流程"
    method_name = "正向验证" if mode == "valid" else method_label
    return {"case_id": f"{prefix}_{ordinal:03d}", "name": api.get("summary") or api.get("operationId") or path, "area": area, "kind": "api", "flow_type": flow_type, "test_method": method_name, "priority": "P0" if mode == "valid" else "P1", "preconditions": ["服务可访问", "测试凭证和数据已准备（如适用）"], "actions": [f"构造 {method.upper()} {path} 请求", "填写测试数据", "发送请求"], "assertions": ([f"HTTP 状态码属于 {expected}"] if expected else ["HTTP 状态码和响应契约需确认"]) + (["错误响应不应泄漏敏感信息"] if negative else ["响应满足接口定义的字段和类型约束"]), "data": payload, "source_refs": source, "tags": ["negative" if negative else "positive", mode], "notes": (["该接口未声明对应错误响应，状态码需要人工确认"] if negative and not [x for x in statuses if x >= 400] else []), "automation_candidate": True, "method": method.upper(), "path": path, "expected_status": expected}

def generate(spec: dict[str, Any], modes: list[str]) -> dict[str, Any]:
    resolver = Resolver(spec); cases=[]; ordinal=1
    for path, path_item in (spec.get("paths") or {}).items():
        shared = path_item.get("parameters", []) if isinstance(path_item, dict) else []
        for method, operation in (path_item or {}).items():
            if method.lower() not in HTTP or not isinstance(operation, dict): continue
            op = dict(operation); op["parameters"] = shared + op.get("parameters", [])
            chosen = modes or ["valid", "missing"]
            for mode in chosen:
                cases.append(make_case(op, mode, mode, ordinal, resolver, path, method)); ordinal += 1
    flow_rank = {"正常流程": 0, "异常流程": 1}
    method_rank = {"正向验证": 0, "场景法": 1, "等价类": 2, "边界值": 3, "非法输入": 4}
    cases.sort(key=lambda c: (flow_rank.get(c.get("flow_type"), 9), method_rank.get(c.get("test_method"), 9), c.get("path", ""), c.get("method", "")))
    counters = {}
    for case in cases:
        prefix = case["case_id"].split("_", 1)[0]
        counters[prefix] = counters.get(prefix, 0) + 1
        case["case_id"] = f"{prefix}_{counters[prefix]:03d}"
    title = spec.get("info", {}).get("title", "OpenAPI")
    return {"schema_version":"1.0", "project":title, "source":{"kind":"openapi", "files":[]}, "assumptions":[], "testcases":cases}

def main(argv=None):
    ap=argparse.ArgumentParser(); ap.add_argument("--spec", required=True); ap.add_argument("--out", required=True); ap.add_argument("--modes", default="valid,missing,empty,wrong_type", help="comma-separated case modes"); args=ap.parse_args(argv)
    doc=generate(read_spec(args.spec), [x.strip() for x in args.modes.split(",") if x.strip()]); Path(args.out).write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8"); print(f"generated {len(doc['testcases'])} cases -> {args.out}")

if __name__ == "__main__": main()
