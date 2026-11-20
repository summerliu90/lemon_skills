import json
import subprocess
import sys
from pathlib import Path

ENGINE = Path(__file__).parents[1] / "scripts" / "test_data_engine.py"

def test_performance_plan():
    p = subprocess.run([sys.executable, str(ENGINE), "perf-plan", "--plan-id", "orders", "--concurrency", "10", "--minutes", "1", "--interface-type", "write", "--slaves", "2"], text=True, capture_output=True)
    assert p.returncode == 0
    result = json.loads(p.stdout)
    assert result["total_records"] == 1200
    assert result["hot_records"] == 1080
    assert result["records_per_slave"] == 600
    assert result["isolation_tag"] == "perf_orders"
