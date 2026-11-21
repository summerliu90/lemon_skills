# TestPilot Knowledge Adapter Contract

## 最小历史案例

```json
{
  "case_id": "HIST-001",
  "title": "string",
  "module": "string|null",
  "business_flow": "string|null",
  "api_signatures": ["POST /orders"],
  "symptoms": ["string"],
  "conditions": ["string"],
  "evidence_refs": ["LOG-001"],
  "root_causes": [{"claim": "string", "status": "verified", "evidence_refs": ["LOG-001"]}],
  "fix": {"summary": "string", "commit": "string|null"},
  "regression": [{"case_id": "TC-001", "result": "passed"}],
  "environment": "string|null",
  "version_range": ["string"],
  "quality": {"verification_complete": true, "last_reviewed": "ISO-8601"}
}
```

## 检索字段优先级

1. 功能模块和业务流程
2. API 方法、路径、错误码和调用链
3. 触发条件、状态和数据特征
4. 版本、配置和环境
5. 用户可见现象和自然语言相似度

自然语言标题相似度只能作为最后一层辅助，不得单独触发历史结论复用。

## TestPilot 当前本地 API 适配

当 TestPilot 在本机运行时，`scripts/testpilot_api.py` 使用只读 GET 请求读取：

```text
GET /api/tasks?type=bug&pageSize=100
GET /api/tasks/{task_id}
GET /api/knowledge?page=1&pageSize=100
```

当前返回字段可映射为：

- `task.input.phenomenon` → 当前缺陷现象
- `task.result.summary` → 历史分析摘要，等级为 `historical-inferred`，除非有验证证据
- `task.result.suggestions` → 历史验证/排查建议
- `knowledge_items[].content` → 历史知识内容
- `knowledge_items[].status` → 只有“已发布”默认进入候选集合；“待审核”只能作为待审资料
- `moduleId` / `moduleLabel` → 功能和模块关联

读取 API 不代表已经完成因果确认。Skill 必须在输出中列出 API 来源、任务 ID、知识条目 ID 和当前差异。

## 匹配审查

每个命中案例需要输出 `matched_fields`、`different_fields`、`transferable_parts` 和 `must_reverify`。历史案例没有验证记录、被重新打开、或环境差异过大时，只能作为背景资料。
