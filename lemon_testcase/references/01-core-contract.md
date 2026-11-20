# 核心契约与模板

本文件定义案例模型、模板使用原则和字段演进方式。字段的完整机器契约仍以 data-contract.md 为准。

## 案例模型

每个案例至少包含 case_id、name、area、kind、priority、preconditions、actions、assertions 和 source_refs。data、tags、notes、automation_candidate、method、path、expected_status 等字段按测试类型选填。

顶层文档应包含 schema_version、project、source、assumptions 和 testcases。来源必须可定位，案例不可脱离来源事实。

## 模板规则

模板只控制字段顺序、展示名称、默认值和输出布局，不改变测试语义。用户指定模板时优先使用；未指定时按输入类型选择默认模板。自定义字段透传，必填字段缺失应在校验阶段报错。

## 字段原则

- actions 是可执行动作列表。
- assertions 是可观察或可断言结果。
- source_refs 用于需求回溯。
- priority 使用 P0、P1、P2、P3。
- 未知事实放入 notes 或 assumptions，并标记待确认。

## 变更规则

新增字段应保持旧案例可解析；修改字段语义需要提升 schema_version。渲染器不得丢弃未知字段，重新导入时应尽量恢复原始案例。
