# 登录 Demo 输入测试矩阵

| 输入文件 | 适配器/脚本 | 目标测试类型 | 预期案例 | 是否可直接验证 |
|---|---|---|---:|---|
| login-prd.md | source_adapters.py | 功能 | 4 | 是 |
| login-online-doc.txt | source_adapters.py | 功能 | 1+ | 是 |
| login-openapi.yaml | openapi_cases.py | 接口 | 4 | 是 |
| login-postman.json | postman_adapter.py | 接口 | 2 | 是 |
| login-legacy-cases.csv | source_adapters.py | 历史用例导入 | 3 | 是 |
| login-page.png | source_adapters.py | UI | 1 | 是 |
| login-ui-notes.md | source_adapters.py | UI/文本 | 1+ | 是 |
| login-state-graph.json | state_matrix.py | 状态迁移 | 5 | 是 |
| login-performance.md | source_adapters.py | 性能计划 | 1+ | 是 |
| login-canonical.json | contract_validator.py | 统一模型 | 2 | 是 |
| login-requirements.json | requirements_mapper.py | 需求覆盖 | 3 | 是 |

DOCX/PDF 输入需要安装对应的可选依赖后再执行。
