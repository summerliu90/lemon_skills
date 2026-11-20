# 输出格式与转换

所有输出从 canonical JSON 渲染。默认输出 Excel；用户明确指定时再输出 Markdown、CSV、XMind 或 JSON。渲染器不得改变测试语义、丢失字段或覆盖未知字段。多行步骤和断言必须可恢复，特殊字符必须转义。

- Markdown：适合评审和版本管理。
- CSV：适合轻量表格交换。
- Excel：适合团队模板、筛选和人工维护。
- XMind：适合桌面思维导图，必须生成有效 ZIP 和入口结构。
- JSON：作为最可靠的回溯和二次转换源。

支持 JSON 到全部格式、表格到 JSON、表格到 XMind，以及 Excel 重新导入 JSON。转换后比较案例数量、编号、步骤、断言和自定义字段。

格式细节见 xmind-detailed.md。
