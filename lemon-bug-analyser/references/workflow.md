# Analysis Workflow and TestPilot Handoff

## 状态机

```text
RECEIVED
  -> TRIAGED
  -> NEEDS_INFO --------------------┐
  -> HISTORY_REVIEW                  |
  -> DIAGNOSING                     |
  -> VERIFYING                      |
  -> ROOT_CAUSE_CONFIRMED           |
  -> REMEDIATION_READY              |
  -> REGRESSION_PENDING             |
  -> MONITORING                     |
  -> CLOSED                         |
                                   -> BLOCKED
```

`NEEDS_INFO` 只表示缺数据，不表示 Bug 不存在；`BLOCKED` 需要明确外部依赖和解除条件；`CLOSED` 必须有修复验证或明确的风险接受记录。

## 门禁

### Intake gate

没有实际结果或期望结果时只能做记录，不能做根因排序。没有环境/版本时可以做初步分类，但必须标记跨环境不确定性。

### History gate

历史匹配要同时比较功能、接口、触发条件、数据状态、版本和环境。匹配分数高不等于结论可迁移；至少有一项当前证据指向历史根因后，才能把历史结论标记为候选。

### Diagnosis gate

每个候选根因都要有预测。没有预测就不是可验证假设；只有描述“可能是网络问题”而没有检查指标、时间窗和预期结果的内容必须降级为低质量警告。

### Closure gate

检查原问题、相邻场景、回归风险、监控观察和数据修复。任何 P0/P1、数据损坏、安全问题或未验证根因不得静默关闭。

## TestPilot 协同

TestPilot 输出建议包含：

- 测试任务、用例、步骤和断言
- 构建、环境、浏览器/设备、账号和数据夹具
- 失败截图、录屏、Console、网络请求和响应
- Trace ID、日志查询窗口、失败次数和成功样本
- 历史 Bug 关联、修复提交和回归结果

本技能给 TestPilot 的验证任务应包含：目标假设、执行前提、动作、采集字段、通过/失败判定和停止条件，而不是只给一句“重新测试”。

## 验证任务格式

```yaml
verification_id: V-001
target_hypothesis: H-001
purpose: "区分接口超时与前端渲染异常"
preconditions: ["使用相同构建", "保留 Trace ID"]
actions: ["执行最小复现步骤", "采集 network waterfall", "重复 10 次"]
collect: ["status", "latency_ms", "response_body", "console_error", "trace_id"]
pass_if: ["响应超过阈值且服务端有对应 timeout 日志"]
fail_if: ["服务端快速成功且仅客户端渲染失败"]
stop_when: "得到支持或排除该假设的证据"
```

## 回填规则

TestPilot 返回结果后，不要只把“通过/失败”写入报告。将每个结果映射到验证任务和假设：通过预期结果时提高支持度，出现反例时降低支持度或标记为排除；没有采集到约定字段时标记 `inconclusive`，不能当作失败或成功。修复后回归结果还必须关联原始触发条件和关闭契约，见 [closure-contract.md](closure-contract.md)。
