---
title: "4. Launch Agent"
summary: "架构图、阅读材料与下级章节。"
weight: 40
ShowToc: false
ShowReadingTime: false
ShowPostNavLinks: false
hideMeta: true
---

## 在任务生命周期中的位置

本章：启动参数来源 → CLI 配置、命令与环境 → 委派运行。

{{< figure src="/images/slime-lifecycle/action-4.svg" link="/images/slime-lifecycle/action-4.svg" alt="当前位置：动作 4：Launch Agent" >}}

[返回项目生命周期总览](/projects/slime/#agent-lifecycle) · [放大当前位置图](/images/slime-lifecycle/action-4.svg)

## 应该看哪些 Python 文件

```text
generate.py：找到 HARNESS_CLS().run(...)
  → common.py：读 BaseHarness.run()
  → claude_code.py 或 codex.py：读配置与启动命令
  → common.py：读 run_agent() 的执行委派
```

下面的路径相对于本地 Slime 源码仓库 `/home/hongshi/projects/slime/`，链接指向本文固定版本 `8c17b676`。按表中顺序阅读；Claude Code 和 Codex 两个分支先选一个即可。

| 顺序 | Python 文件与入口 | 本章重点 |
| --- | --- | --- |
| 1 | [examples/coding_agent_rl/generate.py:182](https://github.com/dextermayhewjd/slime/blob/8c17b676cb57af1d17ee4402e91e9209af84b60b/examples/coding_agent_rl/generate.py#L182) — `generate()` | 找到 `:205` 的 `HARNESS_CLS().run(...)`；向上追踪六项启动输入，确认调用前已经准备了什么 |
| 2 | [slime/agent/harness/common.py:81](https://github.com/dextermayhewjd/slime/blob/8c17b676cb57af1d17ee4402e91e9209af84b60b/slime/agent/harness/common.py#L81) — `BaseHarness.run()` | 先读用户准备 → `HarnessContext` → 写配置 → 启动等待；再读 `:43` 的上下文字段和 `:107` 的 `run_agent()` |
| 3A | [slime/agent/harness/claude_code.py:44](https://github.com/dextermayhewjd/slime/blob/8c17b676cb57af1d17ee4402e91e9209af84b60b/slime/agent/harness/claude_code.py#L44) — `write_config()`、`:57` 的 `launch_and_wait()` | Claude Code 分支：上下文怎样形成配置文件、启动命令和环境变量 |
| 3B | [slime/agent/harness/codex.py:56](https://github.com/dextermayhewjd/slime/blob/8c17b676cb57af1d17ee4402e91e9209af84b60b/slime/agent/harness/codex.py#L56) — `write_config()`、`:69` 的 `launch_and_wait()` | Codex 分支：同样的输入怎样形成另一套 CLI 启动方式 |
| 按需 | [examples/coding_agent_rl/swe.py:77](https://github.com/dextermayhewjd/slime/blob/8c17b676cb57af1d17ee4402e91e9209af84b60b/examples/coding_agent_rl/swe.py#L77) — `get_metadata()`、`:177` 的 `prepare_workspace()` | 不清楚题目、镜像、工作目录和 `PROBLEM_STATEMENT.md` 的来源时，补读这两个函数 |
| 接下章 | [slime/agent/sandbox.py:390](https://github.com/dextermayhewjd/slime/blob/8c17b676cb57af1d17ee4402e91e9209af84b60b/slime/agent/sandbox.py#L390) — `ensure_agent_user()`、`:82` 的 `exec_and_wait()` | 找到 Harness 委派环境操作和执行的接缝；沙箱实现沿 Manage Sandbox 深入，进程启动与等待沿 Exec Commands 深入 |

最短阅读路线：`generate.py` 的调用处 → `common.py` 的 `run()` → 所选 CLI 的 Harness 文件 → `common.py` 的 `run_agent()`。先走通这条链，再补参数来源和沙箱实现。

{{< figure src="diagram.svg" alt="Agent Rollout Adapters and Harnesses" class="slime-diagram" >}}

## 阅读材料

- [1.启动参数和模型入口](<https://github.com/dextermayhewjd/dextermayhewjd.github.io/blob/main/slime_photo/4.Slime%20Core%20Components%20and%20Orchestration/4.1.Agent%20Rollout%20Adapters%20and%20Harnesses/4.Launch%20Agent/1.%E5%90%AF%E5%8A%A8%E5%8F%82%E6%95%B0%E5%92%8C%E6%A8%A1%E5%9E%8B%E5%85%A5%E5%8F%A3.md>)
- [2.主路径和源码函数](<https://github.com/dextermayhewjd/dextermayhewjd.github.io/blob/main/slime_photo/4.Slime%20Core%20Components%20and%20Orchestration/4.1.Agent%20Rollout%20Adapters%20and%20Harnesses/4.Launch%20Agent/2.%E4%B8%BB%E8%B7%AF%E5%BE%84%E5%92%8C%E6%BA%90%E7%A0%81%E5%87%BD%E6%95%B0.md>)
- [3.会话入口和生命周期](<https://github.com/dextermayhewjd/dextermayhewjd.github.io/blob/main/slime_photo/4.Slime%20Core%20Components%20and%20Orchestration/4.1.Agent%20Rollout%20Adapters%20and%20Harnesses/4.Launch%20Agent/3.%E4%BC%9A%E8%AF%9D%E5%85%A5%E5%8F%A3%E5%92%8C%E7%94%9F%E5%91%BD%E5%91%A8%E6%9C%9F.md>)
- [纵向数据流](<https://github.com/dextermayhewjd/dextermayhewjd.github.io/blob/main/slime_photo/4.Slime%20Core%20Components%20and%20Orchestration/4.1.Agent%20Rollout%20Adapters%20and%20Harnesses/4.Launch%20Agent/%E7%BA%B5%E5%90%91%E6%95%B0%E6%8D%AE%E6%B5%81/README.md>)
- [本节 README](<https://github.com/dextermayhewjd/dextermayhewjd.github.io/blob/main/slime_photo/4.Slime%20Core%20Components%20and%20Orchestration/4.1.Agent%20Rollout%20Adapters%20and%20Harnesses/4.Launch%20Agent/README.md>)

[本节资料文件夹](<https://github.com/dextermayhewjd/dextermayhewjd.github.io/tree/main/slime_photo/4.Slime%20Core%20Components%20and%20Orchestration/4.1.Agent%20Rollout%20Adapters%20and%20Harnesses/4.Launch%20Agent>)
