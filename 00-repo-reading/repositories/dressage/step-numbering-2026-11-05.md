# 2026-11-05 · Dressage 步骤编号与范围调整

[项目入口](README.md)

用户要求：

> 好的那么简单先把这三步的scope先逐个产生一下不要写其他的short term function
> 同时考虑吧原来的step
> 更具位置延后处理

本次按推荐阅读位置插入三个前置 scope，旧目录整体顺延，原始阅读事实保留。新编号用于当前阅读路线，不等于这些内容过去也是按此顺序读过。

| 当前编号 | 范围 | 原编号/来源 | 现在的记录状态 |
| --- | --- | --- | --- |
| 000 | generate 整体主线 | 000 | 原有记录保留 |
| [001](topics/01-native-agent-rollout/steps/step-001-task-identity-and-parameters/01-scope.md) | 任务身份与参数准备 | 新增前置 scope | 仅 scope，无新函数/类卡 |
| [002](topics/01-native-agent-rollout/steps/step-002-proxy-client-and-prewarm-claim/01-scope.md) | Proxy 客户端与预热领取 | 新增前置 scope | 仅 scope，无新函数/类卡 |
| [003](topics/01-native-agent-rollout/steps/step-003-paddock-selection/01-scope.md) | 未命中后的身份与 Paddock 准备 | 新增前置 scope | 仅 scope，无新函数/类卡 |
| [004](topics/01-native-agent-rollout/steps/step-004-paddock-environment-preparation/01-scope.md) | Paddock.init 环境初始化 | 原 001 | 已读、按原范围收束；记录整体移入 |
| [005](topics/01-native-agent-rollout/steps/step-005-agent-registration/01-scope.md) | Agent 注册与执行前准备 | 原 002 | scope 与当时准备的记忆快照保留，注册函数未展开 |

## 文件和历史怎样处理

1. 原 step-001-paddock-environment-preparation 整体改为 step-004-paddock-environment-preparation；原 step-002-agent-registration 整体改为 step-005-agent-registration。
2. 所有已有函数/类卡、原话、未知与认识时间保留；本次只搬移目录、修正链接及当前步骤标题/标记。卡片和历史正文里的早期 Step 编号保留原语境，可用本表对照。
3. 原有 02/03 是当时实际阅读形成的记录，不因新增三个尚未展开的 scope 而重造或补入不存在的认识。新增目录只有 01-scope.md；未来开始阅读时再维护对应记忆。
4. 当前先查看新 Step 001 的 scope；生成后三步范围不表示它们已经完成阅读。原 init 不重新记为未读，原注册准备也不记为完成。
5. 运行分支不等于目录顺序：预热命中时可以直接取得 state 并走注册；未命中才进入 Step 003 和 Step 004 对应的代码。
