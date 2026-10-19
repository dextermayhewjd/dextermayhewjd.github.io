# 逐函数记忆模板入口

按记忆类型选择独立的 reference 模板：

- [短期记忆模板](../../.agents/skills/repo-reading-memory/references/short-term-memory-template.md)：本步新形成或修正的理解。
- [长期记忆模板](../../.agents/skills/repo-reading-memory/references/long-term-memory-template.md)：进入本步前继承的累计理解。
- [已填写的紧凑案例](../../.agents/skills/repo-reading-memory/references/translate-function-example.md)：`AnthropicAdapter._translate`。

两种模板正文一致：原话、简短场景与源码、一组 Input → Output、LLM 补充模型、未知、来源。原话已清楚时不再重复写“当前心智模型”；长期只补继承来源，不扩写。

保存路径仍为 `functions/<源码相对路径>/<完整函数名>.md`，只创建实际需要的记录。[完整要求与讨论](../memory-format.md)。
