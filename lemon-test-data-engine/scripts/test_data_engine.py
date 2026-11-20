#!/usr/bin/env python3
"""Small deterministic rule discovery and generation engine."""
import argparse, csv, hashlib, json, random, re, sys, uuid
from datetime import datetime

TOKEN = re.compile(r"\{([a-zA-Z_][\w-]*)(?::([^{}]*))?\}")
IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
CITY_AREA_CODES = {
    "北京市": "110101", "上海市": "310101", "广州市": "440101", "深圳市": "440301",
    "杭州市": "330101", "南京市": "320102", "成都市": "510104", "武汉市": "420102",
    "西安市": "610102", "重庆市": "500103", "长沙市": "430102", "郑州市": "410102",
    "青岛市": "370202", "厦门市": "350203", "苏州市": "320505", "福州市": "350102",
    "合肥市": "340102", "昆明市": "530102", "济南市": "370102", "沈阳市": "210102",
}

def discover(field, samples):
    if not samples: raise ValueError("at least one sample is required")
    if all(re.fullmatch(r"\d{8}", s) for s in samples):
        try:
            dates = [datetime.strptime(s, "%Y%m%d") for s in samples]
            if dates == list(sorted(dates)) and len(set(dates)) == len(dates):
                return {"field": field, "rule": "{date:yyyyMMdd}", "samples": samples,
                        "confidence": 0.94, "questions": []}
        except ValueError:
            pass
    m = [re.match(r"^(.*?)(\d+)$", s) for s in samples]
    if all(m) and len({len(x.group(2)) for x in m}) == 1 and len({x.group(1) for x in m}) == 1:
        prefix, digits = m[0].group(1), [x.group(2) for x in m]
        vals = [int(x) for x in digits]
        if vals == list(range(vals[0], vals[0] + len(vals))):
            candidate, confidence = "{seq:%d}" % len(digits[0]), 0.98
        else:
            candidate, confidence = "{random:%d}" % len(digits[0]), 0.62
        rule = prefix + candidate
        return {"field": field, "rule": rule, "samples": samples, "confidence": confidence,
                "questions": (["Is the changing numeric segment a sequence or random value?"] if "random" in candidate else [])}
    prefix = samples[0]
    for s in samples[1:]:
        i = 0
        while i < min(len(prefix), len(s)) and prefix[i] == s[i]: i += 1
        prefix = prefix[:i]
    if all(re.fullmatch(r"\d{8}", s) for s in samples):
        candidate, confidence = "{date:yyyyMMdd}", 0.72
    else: candidate, confidence = "{value}", 0.25
    rule = prefix + candidate
    return {"field": field, "rule": rule, "samples": samples, "confidence": confidence,
            "questions": (["Is the changing numeric segment a sequence or random value?"] if "random" in candidate else [])}

def fmt_date(pattern, dt):
    return dt.strftime(pattern.replace("yyyy", "%Y").replace("MM", "%m").replace("dd", "%d")
                      .replace("HH", "%H").replace("mm", "%M").replace("ss", "%S"))

def render(template, row, rng, dt, context=None):
    context = context or {}
    def sub(m):
        fn, arg = m.group(1), m.group(2) or ""
        if fn == "date": return fmt_date(arg or "yyyyMMdd", dt)
        if fn == "timestamp": return fmt_date(arg or "yyyyMMddHHmmss", dt)
        if fn == "year": return dt.strftime("%Y")
        if fn == "seq": return str(row).zfill(int(arg or 6))
        if fn == "random": return "".join(str(rng.randrange(10)) for _ in range(int(arg or 6)))
        if fn == "uuid": return str(uuid.UUID(bytes=hashlib.md5(f"{rng.random()}:{row}".encode()).digest()))
        if fn == "choice":
            choices = [x for x in arg.split(",") if x]
            if not choices: raise ValueError("choice requires comma-separated values")
            return rng.choice(choices)
        if fn == "phone": return "1" + rng.choice("3456789") + "".join(str(rng.randrange(10)) for _ in range(9))
        if fn == "idcard": return synthetic_idcard(row, rng, context.get(arg) if arg else None)
        if fn == "email": return f"user{row}@example.test"
        if fn == "name": return f"测试用户{row}"
        if fn == "address": return f"测试省测试市测试区测试路{row}号"
        if fn == "money": return f"{rng.randint(1, 999999) / 100:.2f}"
        if fn == "value": return ""
        if fn == "ref":
            if arg not in context: raise ValueError(f"reference not available: {arg}")
            return str(context[arg])
        raise ValueError(f"unsupported function: {fn}")
    return TOKEN.sub(sub, template)

def synthetic_idcard(row, rng, city=None):
    """Return a synthetic, checksum-valid 18-digit ID; it is not real-person data."""
    birth = f"1990{(row % 12) + 1:02d}{(row % 27) + 1:02d}"
    area_code = CITY_AREA_CODES.get(city, "110101")
    body = area_code + birth + f"{row % 999:03d}"
    weights = (7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2)
    checks = "10X98765432"
    check = checks[sum(int(d) * w for d, w in zip(body, weights)) % 11]
    return body + check

def generate_records(schema, count, seed, dt=None, scenario=None):
    """Generate records from {field: template} or {field: {template: ...}} schema."""
    if not isinstance(schema, dict) or not schema:
        raise ValueError("schema must be a non-empty JSON object")
    rng, dt = random.Random(seed), dt or datetime.now()
    fields = list(schema)
    deps = {field: set() for field in fields}
    for field, spec in schema.items():
        text = json.dumps(spec, ensure_ascii=False) if isinstance(spec, dict) else str(spec)
        deps[field].update(x for x in re.findall(r"\{ref:([^{}]+)\}", text) if x != field)
        if isinstance(spec, dict): deps[field].update(spec.get("depends_on", []))
        unknown = deps[field] - set(fields)
        if unknown: raise ValueError(f"field {field!r} references unknown fields: {sorted(unknown)}")
    order = []
    pending = {k: set(v) for k, v in deps.items()}
    while pending:
        ready = [k for k, v in pending.items() if not v]
        if not ready: raise ValueError(f"cyclic field dependency: {sorted(pending)}")
        order.extend(ready)
        for k in ready: pending.pop(k)
        for v in pending.values(): v.difference_update(ready)
    records = []
    for row in range(1, count + 1):
        record = {}
        for field in order:
            spec = schema[field]
            if isinstance(spec, str): template = spec
            elif isinstance(spec, dict) and scenario and isinstance(spec.get("scenarios", {}).get(scenario), str): template = spec["scenarios"][scenario]
            elif isinstance(spec, dict) and isinstance(spec.get("template"), str): template = spec["template"]
            else: raise ValueError(f"field {field!r} requires a template")
            record[field] = render(template, row, rng, dt, record)
        records.append(record)
    return records

def dependency_plan(schema):
    """Return dependency order without generating data."""
    generate_records(schema, 0, 0)
    deps = {}
    for field, spec in schema.items():
        text = json.dumps(spec, ensure_ascii=False) if isinstance(spec, dict) else str(spec)
        deps[field] = sorted(set(re.findall(r"\{ref:([^{}]+)\}", text)) | set(spec.get("depends_on", []) if isinstance(spec, dict) else []))
    return {"fields": list(schema), "dependencies": deps}

def sql_literal(value):
    if value is None: return "NULL"
    return "'" + str(value).replace("'", "''") + "'"

def to_sql(records, table, batch_id):
    if not IDENTIFIER.fullmatch(table): raise ValueError("table must be a simple SQL identifier")
    if not records: return f"-- batch_id={batch_id}\n"
    fields = list(records[0])
    cols = fields + ["batch_id"]
    lines = [f"-- Generated by lemon-test-data-engine; batch_id={batch_id}", "-- Review target environment before execution.", f"INSERT INTO {table} ({', '.join(cols)}) VALUES"]
    rows = ["(" + ", ".join(sql_literal(record.get(field)) for field in fields) + ", " + sql_literal(batch_id) + ")" for record in records]
    lines.append(",\n".join(rows) + ";")
    return "\n".join(lines) + "\n"

def cleanup_sql(table, batch_id, batch_field="batch_id"):
    if not IDENTIFIER.fullmatch(table) or not IDENTIFIER.fullmatch(batch_field):
        raise ValueError("table and batch-field must be simple SQL identifiers")
    safe = str(batch_id).replace("'", "''")
    return (f"-- Generated by lemon-test-data-engine\n"
            f"-- Review target environment before execution.\n"
            f"-- Only rows from this batch may be removed.\n"
            f"DELETE FROM {table} WHERE {batch_field} = '{safe}';\n")

def verify_records(records, schema):
    errors = []
    if isinstance(records, dict) and isinstance(records.get("data"), list): records = records["data"]
    if not isinstance(records, list): return [{"kind": "input", "message": "data must be a JSON array"}]
    for row, record in enumerate(records, 1):
        missing = [field for field in schema if field not in record]
        errors.extend({"kind": "missing_field", "row": row, "field": field} for field in missing)
    for field, spec in schema.items():
        if isinstance(spec, dict) and spec.get("unique"):
            values = [r.get(field) for r in records if field in r]
            if len(values) != len(set(values)): errors.append({"kind": "uniqueness", "field": field})
    return errors

def performance_plan(concurrency, minutes, interface_type, read_ratio=0.7, hot_ratio=0.9, slave_count=1, plan_id="perf-plan"):
    if concurrency < 0 or minutes < 0: raise ValueError("concurrency and minutes must be non-negative")
    if not 0 <= read_ratio <= 1 or not 0 <= hot_ratio <= 1: raise ValueError("ratios must be between 0 and 1")
    if slave_count < 1: raise ValueError("slave_count must be at least 1")
    seconds = concurrency * minutes * 60
    read = seconds * 1.5
    write = seconds * 2
    if interface_type == "read": total = read
    elif interface_type == "write": total = write
    elif interface_type == "mixed": total = read * read_ratio + write * (1 - read_ratio)
    else: raise ValueError("interface_type must be read, write, or mixed")
    total = int(total + 0.999999)
    hot = int(total * hot_ratio)
    return {"plan_id": plan_id, "interface_type": interface_type, "target_concurrency": concurrency,
            "duration_minutes": minutes, "read_ratio": read_ratio, "hot_ratio": hot_ratio,
            "total_records": total, "hot_records": hot, "cold_records": total - hot,
            "slave_count": slave_count, "records_per_slave": (total + slave_count - 1) // slave_count,
            "isolation_tag": f"perf_{plan_id}"}

def api_script(schema_path, endpoint, method, count, batch_id):
    if not endpoint.startswith("/"): raise ValueError("endpoint must be a relative path")
    if method not in {"POST", "PUT", "PATCH"}: raise ValueError("method must be POST, PUT, or PATCH")
    if count < 0: raise ValueError("count must be non-negative")
    return f'''#!/usr/bin/env python3
"""Generated request runner; review before execution. Batch: {batch_id}"""
import json, os, time, urllib.request

BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8080")
TOKEN = os.environ.get("API_TOKEN", "")
ENDPOINT = {endpoint!r}
METHOD = {method!r}
BATCH_ID = {batch_id!r}
TOTAL = {count}

def load_records():
    with open({schema_path!r}, encoding="utf-8") as f:
        payload = json.load(f)
    return payload if isinstance(payload, list) else payload.get("data", [])

def send(record):
    body = json.dumps({{"batch_id": BATCH_ID, **record}}, ensure_ascii=False).encode()
    request = urllib.request.Request(BASE_URL + ENDPOINT, data=body, method=METHOD,
        headers={{"Content-Type": "application/json", "Authorization": "Bearer " + TOKEN}})
    with urllib.request.urlopen(request, timeout=10) as response:
        return response.status

for index, record in enumerate(load_records()[:TOTAL], 1):
    for attempt in range(3):
        try:
            print(index, send(record)); break
        except Exception as exc:
            if attempt == 2: raise
            time.sleep(2 ** attempt)
'''

def validate_values(values, unique=False, pattern=None):
    errors = []
    if unique and len(values) != len(set(values)):
        errors.append({"kind": "uniqueness", "message": "values are not unique"})
    if pattern:
        for i, value in enumerate(values, 1):
            if not re.fullmatch(pattern, value):
                errors.append({"kind": "format", "row": i, "value": value, "pattern": pattern})
    return errors

def main():
    p = argparse.ArgumentParser(); sub = p.add_subparsers(dest="cmd", required=True)
    l = sub.add_parser("learn"); l.add_argument("--field", required=True); l.add_argument("samples", nargs="+")
    g = sub.add_parser("generate"); g.add_argument("--template", required=True); g.add_argument("--count", type=int, default=1); g.add_argument("--seed", type=int, default=0); g.add_argument("--format", choices=["json","jsonl","csv"], default="json")
    v = sub.add_parser("validate"); v.add_argument("--template", required=True); v.add_argument("--count", type=int, default=1); v.add_argument("--seed", type=int, default=0); v.add_argument("--unique", action="store_true"); v.add_argument("--pattern")
    r = sub.add_parser("records"); r.add_argument("--schema", required=True, help="path to JSON schema"); r.add_argument("--count", type=int, default=1); r.add_argument("--seed", type=int, default=0); r.add_argument("--scenario")
    s = sub.add_parser("sql"); s.add_argument("--schema", required=True); s.add_argument("--table", required=True); s.add_argument("--batch-id", required=True); s.add_argument("--count", type=int, default=1); s.add_argument("--seed", type=int, default=0); s.add_argument("--scenario")
    c = sub.add_parser("cleanup"); c.add_argument("--table", required=True); c.add_argument("--batch-id", required=True); c.add_argument("--batch-field", default="batch_id")
    q = sub.add_parser("verify"); q.add_argument("--schema", required=True); q.add_argument("--data", required=True)
    h = sub.add_parser("perf-plan"); h.add_argument("--plan-id", required=True); h.add_argument("--concurrency", type=int, required=True); h.add_argument("--minutes", type=float, required=True); h.add_argument("--interface-type", choices=["read", "write", "mixed"], required=True); h.add_argument("--read-ratio", type=float, default=0.7); h.add_argument("--hot-ratio", type=float, default=0.9); h.add_argument("--slaves", type=int, default=1)
    k = sub.add_parser("api-template"); k.add_argument("--data", required=True); k.add_argument("--endpoint", required=True); k.add_argument("--method", default="POST"); k.add_argument("--count", type=int, default=1); k.add_argument("--batch-id", required=True)
    d = sub.add_parser("plan"); d.add_argument("--schema", required=True, help="path to JSON schema")
    a = p.parse_args()
    if a.cmd == "learn": out = discover(a.field, a.samples)
    elif a.cmd == "plan":
        with open(a.schema, encoding="utf-8") as f: schema = json.load(f)
        out = dependency_plan(schema)
    elif a.cmd == "cleanup":
        print(cleanup_sql(a.table, a.batch_id, a.batch_field)); return
    elif a.cmd == "verify":
        with open(a.schema, encoding="utf-8") as f: schema = json.load(f)
        with open(a.data, encoding="utf-8") as f: records = json.load(f)
        errors = verify_records(records, schema)
        out = {"valid": not errors, "record_count": len(records) if isinstance(records, list) else 0, "errors": errors}
    elif a.cmd == "perf-plan":
        out = performance_plan(a.concurrency, a.minutes, a.interface_type, a.read_ratio, a.hot_ratio, a.slaves, a.plan_id)
    elif a.cmd == "api-template":
        print(api_script(a.data, a.endpoint, a.method.upper(), a.count, a.batch_id)); return
    elif a.cmd in ("records", "sql"):
        if a.count < 0: raise ValueError("count must be non-negative")
        with open(a.schema, encoding="utf-8") as f: schema = json.load(f)
        records = generate_records(schema, a.count, a.seed, scenario=a.scenario)
        if a.cmd == "sql": print(to_sql(records, a.table, a.batch_id)); return
        unique_fields = [field for field, spec in schema.items() if isinstance(spec, dict) and spec.get("unique")]
        errors = []
        for field in unique_fields:
            values = [record[field] for record in records]
            errors.extend({"field": field, **error} for error in validate_values(values, unique=True))
        out = {"metadata": {"schema": a.schema, "seed": a.seed, "count": a.count}, "valid": not errors, "errors": errors, "data": records}
    elif a.cmd == "generate":
        if a.count < 0: raise ValueError("count must be non-negative")
        rng = random.Random(a.seed); now = datetime.now(); values = [{"value": render(a.template, i, rng, now), "row": i} for i in range(1, a.count+1)]
        out = {"metadata":{"template":a.template,"seed":a.seed,"count":a.count,"generated_at":now.isoformat()},"data":values}
        if a.format == "jsonl":
            for item in values: print(json.dumps(item, ensure_ascii=False))
            return
        if a.format == "csv":
            w = csv.DictWriter(sys.stdout, fieldnames=["row","value"]); w.writeheader(); w.writerows(values); return
    else:
        if a.count < 0: raise ValueError("count must be non-negative")
        rng = random.Random(a.seed); now = datetime.now()
        values = [render(a.template, i, rng, now) for i in range(1, a.count + 1)]
        errors = validate_values(values, a.unique, a.pattern)
        out = {"valid": not errors, "metadata": {"template": a.template, "seed": a.seed, "count": a.count}, "errors": errors}
    print(json.dumps(out, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    try: main()
    except (ValueError, TypeError) as e: print(f"ERROR: {e}", file=sys.stderr); sys.exit(2)
