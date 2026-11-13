# 02 · 本步使用记录

> 编号调整：本目录由 Step 002 顺延为 Step 005。正文中的早期编号、原话及记忆快照保留历史语境；现行顺序见[编号与范围对照](../../../../../../../../step-numbering-2026-11-05.md)。

[本步 scope](../../../../01-scope.md#reading-navigation) · [前序快照](../03-long-term-memory/overview.md)

当前新建的是 scope，注册函数尚未展开，没有提前生成对应函数卡。先调取以下已有记录，支撑调用来路与输入回查：

| 本步用途 | 记录 | 状态 |
| --- | --- | --- |
| 直接调用方 | [blackbox_dispatch.generate](functions/dressage/rollout/generate/blackbox_dispatch.py/generate.md) | 从本步 03 完整调取，保留前序认识与未知 |
| 直接输入 | [SandboxState](classes/dressage/paddock/blackbox/common/state.py/SandboxState.md) | 从本步 03 完整调取，保留字段及来源；调取不算新增理解 |

第一处源码入口是 [Paddock.register_agent](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/paddock/blackbox/paddock.py#L153)。实际阅读后再在本目录保存其记录；其他前序函数仍在 03 按需回查，不全部复制到当前工作列表。
