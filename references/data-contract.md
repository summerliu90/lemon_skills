# 数据契约

## 用例状态

允许值：`passed`、`failed`、`blocked`、`skipped`、`not_run`。报告中的中文状态只作为展示值，内部先归一化。

执行基数不包含 `not_run`。未知状态不能静默归入通过或跳过，应进入审计警告。

## 缺陷字段

至少需要：缺陷编号、标题、优先级、状态、所属模块。P0/P1 或未关闭缺陷还应有影响范围、负责人、计划、上线意见。

## 事实等级

| 等级 | 含义 | 允许用于 Go |
|---|---|---|
| observed | 原始记录直接提供 | 是 |
| derived | 可由已审计数据计算 | 是 |
| inferred | AI 根据上下文推断 | 否，必须标注 |
| missing | 没有数据 | 否 |

## 最小报告字段

```yaml
project: string
version: string
period: string
cases: {total: integer, passed: integer, failed: integer, blocked: integer, skipped: integer, not_run: integer}
bugs: {total: integer, closed: integer, p0: integer, p1: integer}
release_policy: {pass_rate_min: number, p0_max: integer, p1_max: integer}
```
