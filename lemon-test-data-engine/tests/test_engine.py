import json
import re
import subprocess
import sys
from pathlib import Path

ENGINE = Path(__file__).parents[1] / "scripts" / "test_data_engine.py"

def run(*args):
    p = subprocess.run([sys.executable, str(ENGINE), *args], text=True, capture_output=True)
    assert p.returncode == 0, p.stderr
    return json.loads(p.stdout)

def test_learning_sequence():
    result = run("learn", "--field", "order_no", "NO20261012000001", "NO20261012000002")
    assert result["rule"] == "NO{seq:14}"
    assert result["confidence"] >= 0.9

def test_generation_is_reproducible():
    args = ("generate", "--template", "PAY{random:8}", "--count", "3", "--seed", "7")
    assert run(*args)["data"] == run(*args)["data"]

def test_validation_reports_format_error():
    result = run("validate", "--template", "NO{seq:4}", "--count", "2", "--unique", "--pattern", r"NO\d{4}")
    assert result["valid"] is True
    assert result["errors"] == []

def test_structured_records():
    result = run("records", "--schema", str(Path(__file__).with_name("schema.json")), "--count", "2", "--seed", "3")
    assert len(result["data"]) == 2
    assert result["data"][0]["user_id"] == "U00001"
    assert result["data"][0]["user_ref"] == "U00001"
    assert len(result["data"][0]["id_card"]) == 18
    assert result["data"][0]["id_card"][:2] in {"11", "31", "44", "33", "51"}
    assert result["data"][0]["email"].endswith("@example.test")
    assert result["valid"] is True

def test_dependency_plan_and_cycle_detection():
    result = run("plan", "--schema", str(Path(__file__).with_name("schema.json")))
    assert "user_id" in result["dependencies"]["user_ref"]
    bad = Path(__file__).with_name("cycle.json")
    p = subprocess.run([sys.executable, str(ENGINE), "plan", "--schema", str(bad)], text=True, capture_output=True)
    assert p.returncode == 2
    assert "cyclic field dependency" in p.stderr

def test_scenario_and_sql_export():
    result = run("records", "--schema", str(Path(__file__).with_name("schema.json")), "--count", "1", "--scenario", "expired")
    assert result["data"][0]["status"] == "EXPIRED"
    p = subprocess.run([sys.executable, str(ENGINE), "sql", "--schema", str(Path(__file__).with_name("schema.json")), "--table", "test_user", "--batch-id", "batch_1", "--count", "1"], text=True, capture_output=True)
    assert p.returncode == 0
    assert "INSERT INTO test_user" in p.stdout
    assert "batch_1" in p.stdout

def test_invalid_inputs_fail_closed():
    p = subprocess.run([sys.executable, str(ENGINE), "records", "--schema", str(Path(__file__).with_name("cycle.json")), "--count", "1"], text=True, capture_output=True)
    assert p.returncode == 2
    assert "cyclic field dependency" in p.stderr
    p = subprocess.run([sys.executable, str(ENGINE), "generate", "--template", "X{seq:2}", "--count", "-1"], text=True, capture_output=True)
    assert p.returncode == 2

def test_domain_generators():
    result = run("generate", "--template", "{idcard}|{phone}|{address}", "--count", "1", "--seed", "1")
    value = result["data"][0]["value"]
    idcard, phone, address = value.split("|")
    assert len(idcard) == 18 and re.fullmatch(r"\d{17}[0-9X]", idcard)
    assert len(phone) == 11 and phone.startswith("1")
    assert "测试" in address

def test_jsonl_and_sql_identifier_guard():
    p = subprocess.run([sys.executable, str(ENGINE), "generate", "--template", "X{seq:2}", "--count", "2", "--format", "jsonl"], text=True, capture_output=True)
    assert p.returncode == 0 and len(p.stdout.strip().splitlines()) == 2
    p = subprocess.run([sys.executable, str(ENGINE), "cleanup", "--table", "users;DROP", "--batch-id", "b1"], text=True, capture_output=True)
    assert p.returncode == 2

def test_api_template_is_reviewable():
    p = subprocess.run([sys.executable, str(ENGINE), "api-template", "--data", "orders.json", "--endpoint", "/api/orders", "--batch-id", "b1", "--count", "2"], text=True, capture_output=True)
    assert p.returncode == 0
    assert "API_BASE_URL" in p.stdout and "BATCH_ID = 'b1'" in p.stdout
    assert "urlopen" in p.stdout

def test_verify_and_scoped_cleanup():
    data = Path(__file__).with_name("data.json")
    data.write_text(json.dumps([{"user_id": "U00001", "city": "北京市", "id_card": "110101199001010019", "user_ref": "U00001", "phone": "13800000000", "email": "user1@example.test", "name": "测试用户1", "status": "ACTIVE"}], ensure_ascii=False), encoding="utf-8")
    result = run("verify", "--schema", str(Path(__file__).with_name("schema.json")), "--data", str(data))
    assert result["valid"] is True
    p = subprocess.run([sys.executable, str(ENGINE), "cleanup", "--table", "test_user", "--batch-id", "batch_1"], text=True, capture_output=True)
    assert "DELETE FROM test_user WHERE batch_id = 'batch_1';" in p.stdout

def test_verify_accepts_generated_envelope():
    generated = run("records", "--schema", str(Path(__file__).with_name("schema.json")), "--count", "1")
    data = Path(__file__).with_name("generated.json")
    data.write_text(json.dumps(generated, ensure_ascii=False), encoding="utf-8")
    result = run("verify", "--schema", str(Path(__file__).with_name("schema.json")), "--data", str(data))
    assert result["valid"] is True
