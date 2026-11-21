# Verification Action Library

验证动作必须让执行者知道查什么、如何判断和什么时候停止。以下是可组合的动作模板，实际字段仍以当前系统的可观测能力为准。

## 复现与对照

| action | collect | pass signal | reject signal |
|---|---|---|---|
| repeat-minimal-flow | run id, input, result, duration | 相同条件重复出现目标现象 | 多次成功且无触发规律 |
| compare-success-failure | request, response, user, data, trace | 失败样本有稳定差异 | 样本无差异或证据不足 |
| version-bisect | build, config, result | 变更边界与首次失败一致 | 版本边界不一致 |
| environment-matrix | browser/device/region/env | 只在特定环境出现 | 所有环境一致 |

## 关联链

| action | 适用 | 需要检查 |
|---|---|---|
| trace-request | API、线上、超时 | 网关、服务、DB、外部调用耗时 |
| compare-contract | API、兼容性 | 参数、状态码、响应 schema、版本 |
| inspect-state-transition | 业务、数据 | 前置状态、允许迁移、重复迁移、回滚 |
| replay-event | 异步、数据一致性 | 消息 ID、幂等键、消费结果、重试 |

## 数据和性能

| action | 适用 | 保护措施 |
|---|---|---|
| query-read-only | 数据和一致性 | 只读账号、时间范围、脱敏、行数上限 |
| compare-query-plan | 性能 | 保存发布前后计划，不直接改索引 |
| inspect-pool-lock-gc | 性能 | 对齐异常窗口，避免只看当前瞬时值 |
| fault-injection | 降级和恢复 | 测试环境、明确回滚、限制影响范围 |

## AI 专项

| action | 需要固定 | 需要观察 |
|---|---|---|
| replay-same-input | prompt、模型、参数、上下文 | 输出差异、token、工具调用 |
| context-budget-check | 历史消息、检索片段 | 裁剪点、优先级、遗漏约束 |
| tool-call-contract | 工具 schema、权限、超时 | 参数、错误处理、重试和最终回答 |
| model-version-compare | 模型版本、温度、seed（如有） | 同输入差异和安全策略差异 |

## 质量要求

每个验证动作都要补齐：执行者、前置条件、采集字段、预期结果、失败判定、停止条件、证据保存位置和敏感信息处理方式。仅有“检查日志”“重新测试”“看看代码”的动作不合格。
