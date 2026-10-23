# 02 · Step 2 的短期函数记录

[本步入口](../README.md) · [阅读顺序](../01-scope.md) · [前序累计记忆](../03-long-term-memory/overview.md)

本步范围已确定为 `harness.collect_metrics → swe.git_diff`。先进入 Claude Code 的统计收集实现，再随输入来源的追问阅读 `run_hook`，回看 `write_config` 与 `launch_and_wait` 中的准备阶段；这是阅读时的回溯顺序。统计部分收束后，本轮开始阅读 `git_diff`。

| 源码文件 | 函数记录 | 首次接触与当前状态 |
| --- | --- | --- |
| `slime/agent/harness/claude_code.py` | [ClaudeCodeHarness.collect_metrics](functions/slime/agent/harness/claude_code.py/ClaudeCodeHarness.collect_metrics.md) | 2026-10-23，Step 002；输入来源、读取转换与结果用途已经讲解，[按当前目标可收束](../04-flow.md#collect-metrics-reading-checkpoint)；个人理解与未展开的实现细节仍按原记录保留 |
| `slime/agent/harness/compaction.py` | [run_hook](functions/slime/agent/harness/compaction.py/run_hook.md) | 2026-10-23，Step 002；用户已初步串起预先准备、事件触发与写入 JSON；注册、初始化和累计更新的区别为助手本轮补充，触限实现仍未深入 |
| `slime/agent/harness/claude_code.py` | [ClaudeCodeHarness.write_config](functions/slime/agent/harness/claude_code.py/ClaudeCodeHarness.write_config.md) | 调取此前已读记录；用户已复述确认配置与两个事件共用预放脚本，安装阶段和事件输入的区别经补充后尚待反馈；旧版完整保留 |
| `slime/agent/harness/claude_code.py` | [ClaudeCodeHarness.launch_and_wait](functions/slime/agent/harness/claude_code.py/ClaudeCodeHarness.launch_and_wait.md) | 调取此前已读记录；本轮按 `18868a79` 补充统计清零与 CLI 启动次序，旧版完整保留，进程管理细节不扩展 |
| `examples/coding_agent_rl/swe.py` | [git_diff](functions/examples/coding_agent_rl/swe.py/git_diff.md) | 2026-10-23，Step 002；用户已复述比较工作区内容变化，快照与提交历史的区别经澄清后尚待反馈；本地 Git 示例已验证，`_repository_tree` 暂按接口理解 |

后续按实际讨论保存每个函数的调用场景、成对输入输出、简短心智模型与用户原话。需要补清某个内部调用时，再判断是否需要独立卡片；`agent_metrics` 是返回变量，不另建同名函数卡。已有函数需要回顾时，从本步 `03` 调取到这里。
