# C07 · 主 Agent 的 Gateway 路由

| 文档 | 解决的问题 | 状态 |
| --- | --- | --- |
| [07a · Gateway 地址与 Trial 凭证](07a-claude-base-url.md) | Dressage 接管连接时，Harbor 最终使用的地址和凭证是否属于同一条 Trial 路由？ | 本地待审，未提交 |
| [07b · Claude Code 的 settings](07b-claude-settings.md) | Claude 原生 settings 怎样影响已注入的路由？ | 已在备份工作树验证，尚未提交 |
| [07c · Codex 的活动 profile](07c-codex-profile.md) | Codex 最终会使用哪个 provider？ | 已在备份工作树验证，尚未提交 |

开发分支以 C06（`a1087bb`）为基线。07a 卡片记录 Codex 的修前失败、公共连接的配对方法和验收边界。

07b 和 07c 的实验改动保存在 `backup/c07-before-review`。相关评审和提交顺序见 [C06 评审表](../06-harbor-version.md#post-commit-review) 和 [PR-001 提交顺序](../../README.md#review-order)。
