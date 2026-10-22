# 逐函数记忆模板入口

按记忆类型选择独立的 reference 模板：

- [短期记忆模板](../../.agents/skills/repo-reading-memory/references/short-term-memory-template.md)：本步新形成或修正的理解，按[短期 memory skill](../../.agents/skills/repo-reading-short-term-memory/SKILL.md)整理。
- [长期记忆模板](../../.agents/skills/repo-reading-memory/references/long-term-memory-template.md)：进入本步前继承的累计理解。
- [当前认可样例](../../.agents/skills/repo-reading-memory/references/base-adapter-translate.md)：`BaseAdapter._translate`，先对照其结构与场景再填写。

当前结构是：开头定位、LLM 整理的四项、本场景的输入与输出、我的直接表述、尚不清楚、折叠来源。简短通过压缩内容实现，保留当前调用场景；长期只补继承来源，完整保留前序记录。

保存路径仍为 `functions/<源码相对路径>/<完整函数名>.md`，只创建实际需要的记录。[完整要求与讨论](../memory-format.md)。
