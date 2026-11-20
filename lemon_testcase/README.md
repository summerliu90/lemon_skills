# lemon_testcase

面向需求文档、OpenAPI、Postman、设计稿和历史测试表的结构化测试用例生成与导出 skill。

## 能做什么

- 根据 PRD 生成正向、反向、边界、状态和场景案例。
- 根据 OpenAPI/Swagger 生成参数、鉴权、错误码和响应契约案例。
- 根据 Postman Collection 转换已有请求、环境变量和脚本断言。
- 根据设计稿或 OCR 文本生成 UI 布局、交互、状态、响应式和可访问性清单。
- 生成性能测量场景和自动化候选建议。
- 默认输出 Excel；也支持 JSON、Markdown、CSV、XMind 和 HTML 审核页。

## 最短流程

```bash
python scripts/input_router.py --input requirements.md
python scripts/source_adapters.py --input requirements.md --output cases.json
python scripts/contract_validator.py --input cases.json
python scripts/standards_validator.py --input cases.json
python scripts/quality_engine.py --input cases.json
python scripts/lemon_cases.py render --input cases.json --format markdown --output cases.md
```

未指定 --format 时默认生成 Excel：

    python scripts/lemon_cases.py render --input cases.json --output cases.xlsx

## API 流程

```bash
python scripts/openapi_cases.py --spec openapi.yaml --out api-cases.json
python scripts/api_matrix.py audit --input api-cases.json
python scripts/lemon_cases.py render --input api-cases.json --format xmind --output api.xmind
```

## 模板

默认模板在 `assets/templates/`。使用 `template_catalog.py list` 查看模板，使用 `template_engine.py resolve --name api` 查看继承后的字段，使用 `template_validator.py --name api` 校验模板。模板只控制字段和顺序，不改变测试语义。

## 示例

完整示例位于 `examples/`：功能、接口、UI、性能和自动化各有一份 canonical JSON 与可读模板示例。输出文件必须保留 JSON 源文件，便于再次转换和回溯。

## 质量检查

交付前至少执行：

```bash
python scripts/contract_validator.py --input cases.json
python scripts/quality_engine.py --input cases.json
python scripts/roundtrip_suite.py cases.json
python scripts/final_manifest.py --output manifest.json
```

没有事实依据的错误码、性能阈值、隐藏 UI 状态和业务规则必须写入 `notes` 作为待确认项，不得编造。
