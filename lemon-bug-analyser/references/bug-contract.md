# Bug Analysis Contract v1

## 设计目标

这个契约让人工输入、TestPilot 导出、历史知识库和分析结果可以互换。未知值使用 `null` 或空数组，并在 `missing`、`assumptions` 或 `notes` 中解释；不能填入看似合理的默认值。

## 顶层对象

```json
{
  "schema_version": "1.0",
  "bug": {},
  "context": {},
  "evidence": [],
  "relationships": [],
  "history_matches": [],
  "hypotheses": [],
  "verifications": [],
  "conclusion": {},
  "remediation": {},
  "regression": {},
  "audit": {}
}
```

## Bug 对象

```json
{
  "bug_id": "TP-BUG-0001",
  "title": "string",
  "description": "string",
  "expected": "string|null",
  "actual": "string|null",
  "steps": [],
  "trigger_conditions": [],
  "project": "string|null",
  "module": "string|null",
  "business_flow": "string|null",
  "environment": "string|null",
  "version": "string|null",
  "occurred_at": "ISO-8601|null",
  "frequency": "stable|intermittent|once|unknown",
  "report_source": "manual|testpilot|test-run|monitor|log|mixed"
}
```

## 事实等级

| level | 含义 | 可否单独作为根因结论 |
|---|---|---|
| observed | 原始日志、截图、请求、断言直接显示 | 否，需构成因果链 |
| derived | 可由已审计数据计算 | 否，需说明计算过程 |
| historical-verified | 历史案例经过验证的结论 | 否，需检查当前差异 |
| inferred | AI 或分析人员推断 | 不可以 |
| missing | 当前没有证据 | 不可以 |

## Evidence 对象

```json
{
  "evidence_id": "E-001",
  "kind": "log|screenshot|video|api|test-assertion|metric|code-change|config|history|user-report",
  "content": "string",
  "source": "string",
  "locator": "string|null",
  "time_range": {"from": "ISO-8601|null", "to": "ISO-8601|null"},
  "fact_level": "observed",
  "reliability": "high|medium|low|unknown",
  "entities": ["module", "api", "data-object"],
  "supports": ["H-001"],
  "contradicts": [],
  "redaction": {"status": "clean|redacted|needs-review", "items": []}
}
```

## Relationship 对象

```json
{
  "relationship_id": "R-001",
  "from": "user-action",
  "relation": "calls|writes|reads|transitions-to|depends-on|changed-by|observed-as",
  "to": "api-or-service",
  "evidence_refs": ["E-001"],
  "confidence": "high|medium|low|unknown"
}
```

## Hypothesis 对象

```json
{
  "hypothesis_id": "H-001",
  "claim": "string",
  "scope": "module/api/business-rule/data/dependency/environment",
  "prior": "high|medium|low",
  "supporting_evidence": ["E-001"],
  "counter_evidence": [],
  "prediction": "string",
  "verification_plan": ["V-001"],
  "status": "candidate|supported|rejected|verified|inconclusive|not-run",
  "confidence": 0,
  "residual_uncertainty": []
}
```

## 关闭条件

`conclusion.root_causes` 只能引用 `verified` 假设；每个根因至少需要一条当前案例证据、一项可复现或可观测验证结果，以及一个说明反例已处理的备注。证据不足时只能输出 `pending` 或 `blocked`。
