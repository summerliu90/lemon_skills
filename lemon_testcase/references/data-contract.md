# Lemon Case Contract

## 目的

所有生成器和渲染器共享这份数据契约。输入适配器可以保留原文，但输出案例必须归一化到本契约。列表字段使用数组，便于分别显示步骤和断言；标量未知时使用空值并在 `notes` 说明，不使用伪造的默认业务值。

## 顶层文档

```json
{
  "schema_version": "1.0",
  "project": "string",
  "source": {"kind": "prd|openapi|ui|mixed", "files": [], "captured_at": "ISO-8601"},
  "assumptions": [],
  "testcases": []
}
```

## 案例字段

| 字段 | 类型 | 规则 |
|---|---|---|
| case_id | string | 文档内唯一，建议 `LM-F-001`、`LM-API-001` |
| name | string | 描述被验证的行为，不写实现细节 |
| area | string | 模块、资源或页面 |
| kind | string | functional/api/ui/performance/automation |
| priority | string | P0/P1/P2/P3 |
| preconditions | string[] | 执行前必须成立的条件 |
| actions | string[] | 有序、可操作的动作 |
| assertions | string[] | 可观察、可判定的结果 |
| data | object | 输入、变量、边界值或固定夹具 |
| source_refs | string[] | 原文章节、路径、操作编号或图片区域 |
| automation_candidate | boolean | 是否适合稳定自动化 |
| method | string | API 的 HTTP 方法 |
| path | string | API 的路径模板 |
| expected_status | integer[] | API 预期状态码集合 |
| tags | string[] | boundary/auth/state/negative 等 |
| notes | string[] | 假设、风险和待确认项 |

## 归一化规则

1. `preconditions`、`actions`、`assertions`、`source_refs`、`tags`、`notes` 始终输出数组。
2. 表格或旧格式中的 `title` 映射为 `name`，`module/category` 映射为 `area`，`steps` 映射为 `actions`，`expected` 映射为 `assertions`。
3. 字符串中的换行拆成数组；数字、布尔值和对象保留原类型。
4. 没有事实依据的状态码、错误文本和业务计算不得自动补全；可写成“按接口契约返回对应错误”并加待确认说明。
5. 渲染器只能读取契约，不应改变测试语义。
