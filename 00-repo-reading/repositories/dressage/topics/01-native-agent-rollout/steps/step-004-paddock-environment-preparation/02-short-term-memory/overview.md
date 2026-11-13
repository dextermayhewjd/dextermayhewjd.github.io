# 02 · 本步函数与类记录

> 编号调整：本目录由 Step 001 顺延为 Step 004。正文中的早期编号、原话及记忆快照保留历史语境；现行顺序见[编号与范围对照](../../../../../step-numbering-2026-11-05.md)。

[本步入口](../README.md) · [本步 scope](../01-scope.md#reading-navigation) · [前序快照](../03-long-term-memory/overview.md)

| 本步角色 | 函数或类记录 | 来源与状态 |
| --- | --- | --- |
| 健康检查回查 | [BlackboxServerClient.health](functions/dressage/paddock/blackbox/client.py/BlackboxServerClient.health.md) | 一次 HTTP 健康请求；正常结束后继续 state，失败交给 init 清理 |
| 刚读接口 | [SandboxProvider.get_public_url](functions/dressage/sandbox/provider.py/SandboxProvider.get_public_url.md) | 用户已概括取得 endpoint 的用途；调用条件和失败细节仍按后续反馈确认 |
| 前一接口 | [SandboxProvider.create](functions/dressage/sandbox/provider.py/SandboxProvider.create.md) | 以用户提供的 Paddock 调用代码为主例；保留共同输入输出、就绪与失败责任 |
| 接口总览 | [SandboxProvider](classes/dressage/sandbox/provider.py/SandboxProvider.md) | 用户已概括协议及六项操作；name 属性与结构匹配边界已补充，create 调用例子在方法卡 |
| 本步父流程 | [BlackboxAgentPaddock.init](functions/dressage/paddock/blackbox/paddock.py/BlackboxAgentPaddock.init.md) | 用户已概括环境取得的总体作用；正常路径已收束，lease/state 精确区别与异常机制的未知保留 |
| 上层回查 | [blackbox_dispatch.generate](functions/dressage/rollout/generate/blackbox_dispatch.py/generate.md) | 从本步 03 调取；保留已复述的主线及未解决区别 |
| 字段回查 | [SandboxSpec](classes/dressage/sandbox/types.py/SandboxSpec.md) | 用户已复述环境请求的整体作用；标识和 metadata 的精确含义待反馈 |
| 字段回查 | [SandboxServiceSpec](classes/dressage/sandbox/types.py/SandboxServiceSpec.md) | 用户已联系到访问需求；后端选择、访问方向与实际地址的区别已校准，待反馈 |
| 返回记录 | [SandboxLease](classes/dressage/sandbox/types.py/SandboxLease.md) | 用户明确已看过 Endpoint；Lease 的对象关系按需回顾，未标记全部掌握 |
| 交付状态 | [SandboxState](classes/dressage/paddock/blackbox/common/state.py/SandboxState.md) | 本轮展开；说明怎样从 lease 得到并交回 generate，理解待反馈 |

init 与上述接口/数据类属于本步 02；generate 从本步 03 调入作上层回查。具体实现的完整说明在 [references/local-bwrap-create.md](../references/local-bwrap-create.md)，不再计入当前短期函数索引。
