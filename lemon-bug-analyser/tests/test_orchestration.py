#!/usr/bin/env python3
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "bug_analyser.py"
API_SPEC = spec_from_file_location("testpilot_api", ROOT / "scripts" / "testpilot_api.py")
API = module_from_spec(API_SPEC); API_SPEC.loader.exec_module(API)

def test_no_history_routes_to_professional():
    with tempfile.TemporaryDirectory() as tmp:
        output = Path(tmp) / "context.json"
        subprocess.run([sys.executable, str(SCRIPT), "analyse", "--input", str(ROOT / "examples" / "performance-regression.json"), "--output", str(output)], check=True)
        data = json.loads(output.read_text())
        assert data["audit"]["history_route"] == "professional-diagnosis"
        assert data["audit"]["professional_route"]

def test_history_route_is_explicitly_conservative():
    with tempfile.TemporaryDirectory() as tmp:
        history = Path(tmp) / "matches.json"
        output = Path(tmp) / "context.json"
        history.write_text(json.dumps({"matches": [{"case_id": "H-1", "score": 0.91, "must_reverify": False}]}))
        subprocess.run([sys.executable, str(SCRIPT), "analyse", "--input", str(ROOT / "examples" / "performance-regression.json"), "--history", str(history), "--output", str(output)], check=True)
        data = json.loads(output.read_text())
        assert data["audit"]["history_route"] == "history-candidate"
        assert "current evidence" in data["audit"]["history_warning"]

def test_api_retrieval_shape_without_network():
    original = API.get_json
    def fake(base, path, params=None, timeout=5):
        if path == "/api/tasks": return {"items": [{"id": "task_bug_001"}]}
        if path == "/api/knowledge": return {"items": [{"id": "kb_001", "status": "已发布"}]}
        return {"id": "task_bug_001", "result": {"summary": "historical"}}
    API.get_json = fake
    try:
        result = API.retrieve("http://127.0.0.1:3344", "task_bug_001")
        assert result["retrieval"]["task_count"] == 1
        assert result["task"]["id"] == "task_bug_001"
    finally:
        API.get_json = original

if __name__ == "__main__":
    test_no_history_routes_to_professional(); test_history_route_is_explicitly_conservative(); test_api_retrieval_shape_without_network(); print("orchestration test passed")
