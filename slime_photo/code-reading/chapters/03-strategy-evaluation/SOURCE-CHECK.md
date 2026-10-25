# Rollout 接入与奖励：源码核对

- 核对日期：2026-10-25。
- 本地仓库：`/home/fredkeira/projects/slime`。
- 本地 HEAD：`18868a79b0b083a093798a94ed0f8cb4f71b9c14`；本次只读查询 `THUDM/slime main` 得到同一提交，没有更新本地源码。
- 本文只核对已展开的接入与返回边界；不将文件存在、静态关系或文档生成当作运行证据。

| 解释内容 | 固定源码 |
| --- | --- |
| 示例使用 fully-async rollout 与 Coding Agent 自定义生成 | [run_qwen38_27b_fully_async.sh:165–167](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/run_qwen38_27b_fully_async.sh#L165-L167) |
| group 为单个待生成 Sample 创建任务 | [sglang_rollout.py:419–427](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sglang_rollout.py#L419-L427) |
| 输入 Sample 的数据字段、状态与生成路径 | [types.py:106–170](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/utils/types.py#L106-L170) |
| 选择函数、检查参数、创建异步调用并等待 | [sglang_rollout.py:338–349](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sglang_rollout.py#L338-L349) |
| 由导入路径取得属性 | [misc.py:50–59](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/utils/misc.py#L50-L59) |
| 被调用的 Coding Agent 包装与正常任务返回 | [generate.py:225–251](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/generate.py#L225-L251)、[300–358](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/generate.py#L300-L358) |
| hook、组评分边界、单样本与列表的奖励判断 | [sglang_rollout.py:353–380](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sglang_rollout.py#L353-L380) |
| 空列表仍进入批量接口；自定义与默认处理 | [rm_hub/__init__.py:99–110](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/rm_hub/__init__.py#L99-L110) |
| state 的共享实例及执行控制成员 | [GenerateState:84–140](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sglang_rollout.py#L84-L140)、[SingletonMeta:62–76](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/utils/misc.py#L62-L76) |
| pacer 分批唤醒；区别于并发上限和手动暂停 | [AsyncPacer:8–42](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/utils/async_utils.py#L8-L42) |
| 生成许可在 hook、RM 之前由 finally 释放 | [sglang_rollout.py:329–378](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sglang_rollout.py#L329-L378) |
| 两类包装登记共享状态，供中止逻辑使用 | [258–285](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sglang_rollout.py#L258-L285)、[442–465](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sglang_rollout.py#L442-L465) |
| 生成器和 hook 新建 Sample 时继承原任务上下文 | [transport.py:207–230](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/data/transport.py#L207-L230) |
| aborted 为布尔值；DP 上下文选择最少计数并在退出减回 | [reset 与 DP 上下文:123–140](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sglang_rollout.py#L123-L140)、[abort:442–448](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sglang_rollout.py#L442-L448) |

本轮未执行生成或评分契约测试；并发、取消、评分插件、失败结果及真实环境仍需各自的行为证据。文档构建与链接检查只用于验证阅读材料。
