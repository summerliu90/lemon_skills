# 使用、CLI 与示例

## 标准流程

识别输入并提取来源；生成 canonical JSON；运行 contract_validator、standards_validator 和 quality_engine；运行覆盖矩阵或需求映射；渲染目标格式；回读输出并生成交付清单。

## 常用命令

    python scripts/input_router.py --input requirements.md
    python scripts/source_adapters.py --input requirements.md --output cases.json
    python scripts/contract_validator.py --input cases.json
    python scripts/standards_validator.py --input cases.json
    python scripts/quality_engine.py --input cases.json
    python scripts/lemon_cases.py render --input cases.json --format markdown --output cases.md

OpenAPI 使用 openapi_cases.py；Postman 使用 source_adapters.py；表格和 XMind 使用 format_convert.py 或 lemon_cases.py。

## 示例

登录功能样例位于 examples/demo，包含 PRD、OpenAPI、Postman、CSV、UI 截图、性能说明、状态图和 canonical JSON。

## 交付清单

说明输入来源、案例数量、测试类型、优先级分布、覆盖范围、模板、输出文件、待确认事项和质量校验结果。必须保留 JSON 源文件。
