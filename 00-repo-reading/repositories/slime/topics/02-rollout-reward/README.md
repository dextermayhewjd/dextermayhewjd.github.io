# 02 · Rollout 接入与奖励

[Slime 项目入口](../../README.md) · [当前进度](../../../../../slime_photo/code-reading/repo-reading-route.md#当前接续) · [前一主题](../01-coding-agent-rl/README.md)

## 核心问题

已经读过的 Coding Agent 怎样作为生成函数接入 Slime？它交回的样本由谁接收，什么时候还需要框架评分？

本主题先沿一个新任务的正常训练路径，接清“选择生成函数 → 等待结果 → 判断奖励归属 → 返回”。生成与评分的可替换接口是本主题重点；成组并发、持续调度和训练消费分别在后续主题展开。

## 主入口与源码范围

| 入口 | 要解决的问题 |
| --- | --- |
| [sglang_rollout.py::generate_and_rm](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sglang_rollout.py#L289-L380) | 怎样选中生成函数，接收 Sample / Sample 列表，并判断是否补评分 |
| [rm_hub/__init__.py](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/rm_hub/__init__.py#L55-L110) | 后续沿实际需要展开单样本与批量评分接口 |
| [Coding Agent generate](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/generate.py#L225-L251) | 作为已读实现回接，内部主线见前一主题 |

## 步骤索引

| 步骤 | 本步问题 | 入口 |
| --- | --- | --- |
| Step 010 | 自定义生成函数怎样接入，生成后谁负责评分 | [阅读范围与记录](steps/step-010-generate-and-rm/README.md) |

[网页讲解](http://localhost:1313/projects/slime/rollout-reward/)随实际阅读补充。步骤编号延续前一主题，前序记忆按上一实际步骤的 `03 + 02` 继承；本页只作主题与步骤索引。
