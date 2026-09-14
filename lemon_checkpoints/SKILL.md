---
name: lemon-checkpoints
description: 把产品需求、原型、截图或用户故事转成按风险排序的测试执行清单，同时保留规则证据、待确认事项和覆盖地图。适合登录、交易、审批、数据处理及智能功能的测试分析；默认输出 Excel，也可按需输出 Markdown 或飞书/XMind 大纲。不用于编写逐步测试用例和完整测试计划。
metadata:
  version: "1.2"
  author: summer
---

# Lemon Checkpoints

测试人员拿到的材料经常不完整。先把“已经看到的事实”和“尚未确认的规则”分开，才能避免用经验替产品做决定。这个 skill 以业务链路和失败风险组织测试工作，测试方向只负责查漏，不直接决定排版。

## 处理框架

按下面四层形成结果：

1. **输入底稿**：说明业务背景、测试对象、可见证据和材料限制。
2. **风险路线**：按用户目标划分业务链路，标出阻断点、数据风险和安全风险。
3. **执行清单**：把测试点分成首轮冒烟、重点验证、扩展检查三个批次。
4. **覆盖地图**：用标准测试方法检查遗漏，记录已覆盖、待补充和不适用项。

待确认问题必须单独形成可跟踪清单，不能只混在输入底稿或测试点的“依据”列中。每条问题至少包含：问题编号、需要确认的具体规则、影响的测试点、风险或影响、负责人、状态、确认结论。没有负责人信息时保留空白，不得省略字段。

详细字段和判断规则见 [分析模型](references/analysis-model.md)。标准测试方向见 [覆盖地图](references/coverage-map.md)。

## 输入不完整时

- 截图、原型或一句话需求可以直接分析，但只能把可见内容列为事实。
- 对登录结果、接口返回、数据写入、权限、失败限制等不可见行为，写成“验证建议”并关联待确认问题。
- 只问会改变测试结论的问题，最多 6 个。其余问题放入交付物，避免中断工作。

## 生成测试点

每条测试点必须回答五件事：触发什么情况、使用什么数据、检查什么结果、失败会造成什么影响、依据来自哪里。相同目标和相同结果的场景合并；边界、权限、并发和恢复路径不能因为材料缺失而直接省略，高风险但无依据的内容作为建议保留。

优先级使用 `S0` 至 `S3`：

- `S0`：核心功能、安全或数据完整性问题，失败会阻止上线。
- `S1`：主要业务能力受损，对大量用户或日常操作有明显影响。
- `S2`：影响有限，有绕行方案。
- `S3`：低频或低影响，可以后续处理。

## 专项处理

- 出现金额、计费、库存、额度或算法时，读取 [计算类场景](references/special-scenarios.md#计算类场景)。
- 出现大模型、内容生成、推荐、识别或对话时，读取 [智能功能场景](references/special-scenarios.md#智能功能场景)。

## 交付方式

默认输出 **Excel**（`.xlsx`）。用户明确要求 Markdown、脑图或多种格式时，再按 [交付规范](references/output-formats.md) 切换。Excel 工作表固定为：执行看板、测试清单、待确认、规则证据、覆盖地图。“待确认”必须是独立工作表，即使当前没有问题也要保留表头并注明“无”。

Agent 落盘约定：未指定路径时，写到工作区 `output/lemon-checkpoints/<需求简称>-测试执行清单.xlsx`；用户指定路径时以用户为准。

本地辅助脚本（`build` / `draft` 默认 `--format excel`）：

```bash
python3 scripts/lemon_checkpoints.py scan -i 需求.md -o 输入检查.md
python3 scripts/lemon_checkpoints.py build -i 需求.md -o 执行清单.xlsx
python3 scripts/lemon_checkpoints.py build -i 需求.md -o 执行清单.md --format markdown
python3 scripts/lemon_checkpoints.py build -i 需求.md -o 测试脑图.md --format mindmap
python3 scripts/lemon_checkpoints.py prompt -i 需求.md -o 可复制提示词.md
```

为兼容 v1.1，`inspect` 等同于 `scan`，`draft` 等同于 `build`，`--layout` 等同于 `--format`。脚本负责识别、分组和生成底稿，不代替人工或模型完成业务判断。
