# 登录功能 Demo 数据

该目录提供一套可用于验证 `lemon_testcase` 输入、生成、模板和输出能力的最小登录场景。

## 文件说明

| 文件 | 用途 |
|---|---|
| `login-prd.md` | 功能测试和边界测试输入 |
| `login-openapi.yaml` | API schema 驱动生成输入 |
| `login-postman.json` | Postman Collection 解析输入 |
| `login-legacy-cases.csv` | 历史表格导入和格式转换输入 |
| `login-ui-notes.md` | UI 测试补充说明 |
| `login-page.png` | UI 截图输入 |

## 推荐验证命令

```bash
# PRD
python ../../scripts/source_adapters.py --input login-prd.md --output /tmp/login-prd.json

# OpenAPI
python ../../scripts/openapi_cases.py --spec login-openapi.yaml --out /tmp/login-api.json

# Postman
python ../../scripts/postman_adapter.py --input login-postman.json --output /tmp/login-postman.json

# 历史 CSV
python ../../scripts/source_adapters.py --input login-legacy-cases.csv --output /tmp/login-csv.json

# UI
python ../../scripts/source_adapters.py --input login-page.png --output /tmp/login-ui.json

# 输出和验证
python ../../scripts/lemon_cases.py render --input /tmp/login-api.json --format xmind --output /tmp/login-api.xmind
python ../../scripts/roundtrip_suite.py /tmp/login-api.json
```

所有密码、token、URL 和账号均为演示占位值，不可用于真实系统。
