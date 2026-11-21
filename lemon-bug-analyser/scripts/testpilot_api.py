#!/usr/bin/env python3
"""Read-only TestPilot API connector for local bug and knowledge retrieval."""
import argparse
import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from pathlib import Path

def get_json(base_url, path, params=None, timeout=5):
    url = base_url.rstrip("/") + path
    if params: url += "?" + urlencode(params)
    request = Request(url, headers={"Accept": "application/json"}, method="GET")
    with urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))

def retrieve(base_url, task_id=None, page_size=100):
    tasks = get_json(base_url, "/api/tasks", {"type": "bug", "pageSize": page_size})
    knowledge = get_json(base_url, "/api/knowledge", {"page": 1, "pageSize": page_size})
    selected = None
    if task_id:
        selected = get_json(base_url, "/api/tasks/" + task_id)
    history_cases = []
    for item in knowledge.get("items", []):
        history_cases.append({
            "case_id": item.get("id"),
            "title": item.get("title"),
            "module": item.get("moduleLabel") or item.get("moduleId"),
            "business_flow": item.get("title"),
            "api_signatures": [],
            "conditions": [],
            "symptoms": [item.get("content", "")],
            "root_causes": [],
            "quality": {"verification_complete": item.get("status") == "已发布"},
            "source": "testpilot-knowledge",
            "source_status": item.get("status")
        })
    for item in tasks.get("items", []):
        result = item.get("result") or {}
        history_cases.append({
            "case_id": item.get("id"),
            "title": item.get("title"),
            "module": item.get("moduleLabel") or item.get("moduleId"),
            "business_flow": item.get("input", {}).get("phenomenon", ""),
            "api_signatures": [], "conditions": [],
            "symptoms": [item.get("input", {}).get("phenomenon", "")],
            "root_causes": [{"claim": result.get("summary", ""), "status": "historical-verified"}],
            "quality": {"verification_complete": item.get("status") == "已完成" and item.get("reviewStatus") == "审核通过"},
            "source": "testpilot-bug-task",
            "source_status": item.get("knowledgeStatus")
        })
    return {
        "source": "testpilot-api",
        "base_url": base_url.rstrip("/"),
        "task": selected,
        "bug_tasks": tasks.get("items", []),
        "knowledge_items": knowledge.get("items", []),
        "history_cases": history_cases,
        "retrieval": {"task_count": len(tasks.get("items", [])), "knowledge_count": len(knowledge.get("items", [])), "task_id": task_id}
    }

def main():
    p = argparse.ArgumentParser(); p.add_argument("--base-url", default="http://127.0.0.1:3344"); p.add_argument("--task-id"); p.add_argument("--output", required=True)
    a = p.parse_args(); result = retrieve(a.base_url, a.task_id); Path(a.output).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

if __name__ == "__main__": main()
