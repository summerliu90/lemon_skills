# 脚本职责地图

当前根目录脚本保留为稳定 CLI 入口，避免破坏已有命令。下面按职责说明其归属，后续新增脚本应按该分类放入对应子目录。

## 输入

input_router.py、source_adapters.py、import_sources.py、document_extractors.py、postman_adapter.py、openapi_cases.py。

## 生成与场景

case_generators.py、scenario_planner.py、state_matrix.py、data_matrix.py、fixture_builder.py、requirements_mapper.py。

## 输出与格式

lemon_cases.py、format_convert.py、advanced_renderers.py、excel_bridge.py、excel_roundtrip.py、format_auditor.py。

## 质量与审计

contract_validator.py、standards_validator.py、quality_engine.py、audit_cases.py、coverage_report.py、api_matrix.py、security_checker.py、dependency_probe.py。

## 模板与差异

template_catalog.py、template_engine.py、template_validator.py、case_diff.py。

## 支持工具

roundtrip_check.py、roundtrip_suite.py、report_builder.py、final_manifest.py。

## 结构原则

根目录入口优先保证兼容；职责相同的脚本共享 canonical JSON，不直接互相复制业务逻辑；输出脚本只负责渲染，质量脚本只负责报告问题。
