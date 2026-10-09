---
title: "5. Manage Sandbox"
summary: "架构图、阅读材料与下级章节。"
weight: 50
ShowToc: false
ShowReadingTime: false
ShowPostNavLinks: false
hideMeta: true
---

## 在任务生命周期中的位置

本章：环境能力贯穿准备、运行、收尾；不是仅在启动前执行的一步。

{{< figure src="/images/slime-lifecycle/action-5.svg" link="/images/slime-lifecycle/action-5.svg" alt="当前位置：动作 5：Manage Sandbox" >}}

[返回项目生命周期总览](/projects/slime/#agent-lifecycle) · [放大当前位置图](/images/slime-lifecycle/action-5.svg)

## 应该看哪些 Python 文件

```text
sandbox.py：认识接口和 E2BSandbox 实现
  → generate.py：读 boot_agent_sandbox()，看谁创建和释放
  → Harness 文件：看调用方怎样使用 sb
  → 回到 sandbox.py：看具体操作怎样落实
```

下面的路径相对于本地 Slime 源码仓库 `/home/hongshi/projects/slime/`，链接指向本文固定版本 `8c17b676`。本章的主要实现集中在 `sandbox.py`，其余文件帮助你找到创建者和调用者。

| 顺序 | Python 文件与入口 | 本章重点 |
| --- | --- | --- |
| 1 | [slime/agent/sandbox.py:28](https://github.com/dextermayhewjd/slime/blob/8c17b676cb57af1d17ee4402e91e9209af84b60b/slime/agent/sandbox.py#L28) — `Sandbox`；`:160` 的 `E2BSandbox` | 先认出 `exec()`、`write_file()`、`read_file()` 接口；再读 `:281` 的创建、`:302` 的释放、`:309` 的命令执行、`:342` / `:380` 的文件读写实现 |
| 2 | [examples/coding_agent_rl/generate.py:96](https://github.com/dextermayhewjd/slime/blob/8c17b676cb57af1d17ee4402e91e9209af84b60b/examples/coding_agent_rl/generate.py#L96) — `boot_agent_sandbox()` | 谁创建沙箱、调用 `install_cli()`、交出 `sb` 并在退出时释放；再看 `:203` 的任务代码如何进入这个上下文 |
| 3 | [slime/agent/harness/common.py:81](https://github.com/dextermayhewjd/slime/blob/8c17b676cb57af1d17ee4402e91e9209af84b60b/slime/agent/harness/common.py#L81) — `BaseHarness.run()` | 找到 `ensure_agent_user()` 的调用；再读 `:107` 的日志目录准备、`:125` / `:154` 的 CLI 和 Node 安装怎样使用沙箱接口 |
| 4A | [slime/agent/harness/claude_code.py:36](https://github.com/dextermayhewjd/slime/blob/8c17b676cb57af1d17ee4402e91e9209af84b60b/slime/agent/harness/claude_code.py#L36) — `install_cli()`、`:44` 的 `write_config()` | Claude Code 分支向沙箱提交哪些安装与配置操作；先选这一分支或下一分支 |
| 4B | [slime/agent/harness/codex.py:48](https://github.com/dextermayhewjd/slime/blob/8c17b676cb57af1d17ee4402e91e9209af84b60b/slime/agent/harness/codex.py#L48) — `install_cli()`、`:56` 的 `write_config()` | Codex 分支向沙箱提交哪些安装与配置操作 |
| 按需 | [examples/coding_agent_rl/swe.py:177](https://github.com/dextermayhewjd/slime/blob/8c17b676cb57af1d17ee4402e91e9209af84b60b/examples/coding_agent_rl/swe.py#L177) — `prepare_workspace()`、`:230` 的 `git_diff()` | 工作区和题目文件怎样准备，任务结束后怎样从沙箱收集代码 diff |

`sandbox.py` 建议分两遍读：第一遍读接口、创建、释放、命令和文件操作，以及 `:390` 的 `ensure_agent_user()`；第二遍再读 `:237` 的 `_rpc_retry()`。`:82` 的 `exec_and_wait()` 是与 Exec Commands 相接的部分，先认出调用入口，再到动作 6 细读启动脚本与等待机制。

两章会出现同一批文件：Launch Agent 看 Harness 怎样组织启动要求；Manage Sandbox 看这些要求怎样经 `sb` 落到执行环境。章节按职责划分，一个 Python 文件可以同时参与多个动作。

{{< figure src="diagram.svg" alt="Agent Rollout Adapters and Harnesses" class="slime-diagram" >}}

## 阅读材料

- [1.命令和文件操作](<https://github.com/dextermayhewjd/dextermayhewjd.github.io/blob/main/slime_photo/4.Slime%20Core%20Components%20and%20Orchestration/4.1.Agent%20Rollout%20Adapters%20and%20Harnesses/5.Manage%20Sandbox/1.%E5%91%BD%E4%BB%A4%E5%92%8C%E6%96%87%E4%BB%B6%E6%93%8D%E4%BD%9C.md>)
- [2.主路径和源码函数](<https://github.com/dextermayhewjd/dextermayhewjd.github.io/blob/main/slime_photo/4.Slime%20Core%20Components%20and%20Orchestration/4.1.Agent%20Rollout%20Adapters%20and%20Harnesses/5.Manage%20Sandbox/2.%E4%B8%BB%E8%B7%AF%E5%BE%84%E5%92%8C%E6%BA%90%E7%A0%81%E5%87%BD%E6%95%B0.md>)
- [3.创建入口和生命周期](<https://github.com/dextermayhewjd/dextermayhewjd.github.io/blob/main/slime_photo/4.Slime%20Core%20Components%20and%20Orchestration/4.1.Agent%20Rollout%20Adapters%20and%20Harnesses/5.Manage%20Sandbox/3.%E5%88%9B%E5%BB%BA%E5%85%A5%E5%8F%A3%E5%92%8C%E7%94%9F%E5%91%BD%E5%91%A8%E6%9C%9F.md>)
- [纵向数据流](<https://github.com/dextermayhewjd/dextermayhewjd.github.io/blob/main/slime_photo/4.Slime%20Core%20Components%20and%20Orchestration/4.1.Agent%20Rollout%20Adapters%20and%20Harnesses/5.Manage%20Sandbox/%E7%BA%B5%E5%90%91%E6%95%B0%E6%8D%AE%E6%B5%81/README.md>)
- [本节 README](<https://github.com/dextermayhewjd/dextermayhewjd.github.io/blob/main/slime_photo/4.Slime%20Core%20Components%20and%20Orchestration/4.1.Agent%20Rollout%20Adapters%20and%20Harnesses/5.Manage%20Sandbox/README.md>)

[本节资料文件夹](<https://github.com/dextermayhewjd/dextermayhewjd.github.io/tree/main/slime_photo/4.Slime%20Core%20Components%20and%20Orchestration/4.1.Agent%20Rollout%20Adapters%20and%20Harnesses/5.Manage%20Sandbox>)
