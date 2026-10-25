# 01 · Coding Agent RL：generate 主线与 agent 组件

[Slime 项目入口](../../README.md) · [当前进度](../../../../../slime_photo/code-reading/repo-reading-route.md#当前接续) · [后续模块顺序](../../slime后续阅读顺序/current-goal-slime-reading-order.md)

## 核心问题

一道代码任务怎样获得会话和运行环境、启动 Agent、请求模型、留下代码改动、得到评测奖励，并交付训练样本。

本主题收纳原 Step 000–009。它们覆盖的是这条任务主线实际涉及的代码；不能据此认定整个 `slime/agent/` 已完整读完。各步已确认的深度、未知与实际运行状态继续按原记录保留。

## 主入口与源码范围

主入口是 `examples/coding_agent_rl/generate.py::generate → _generate`，其中 `_generate` 组织单题执行。下面的目录和文件是沿调用需要进入的实现。

| 范围 | 主要承担什么 |
| --- | --- |
| [examples/coding_agent_rl/generate.py](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/generate.py) | 单题编排、服务与会话准备、沙箱使用和结果交接 |
| [examples/coding_agent_rl/swe.py](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/swe.py) | 工作区、补丁、评测与奖励 |
| [slime/agent/harness/](https://github.com/THUDM/slime/tree/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/harness) | CLI 配置、启动、等待及统计 |
| [slime/agent/adapters/](https://github.com/THUDM/slime/tree/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters) 与 `aiohttp_threaded.py` | HTTP 接入、协议适配、模型请求和会话管理 |
| [slime/agent/trajectory.py](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/trajectory.py) | 消息轨迹、路径与训练样本导出 |
| [slime/agent/sandbox.py](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/sandbox.py) 与示例目录中的沙箱适配 | 环境操作、执行等待及资源生命周期 |

## 步骤索引

编号保留真实阅读历史，下面不是程序按时间运行的顺序。

| 步骤 | 当时围绕的问题 | 入口 |
| --- | --- | --- |
| Step 000 | Coding Agent 的核心骨架与职责 | [步骤记录](steps/step-000-coding-agent/README.md) |
| Step 001 | 一次模型请求怎样处理并留下轨迹 | [步骤记录](steps/step-001-harness-to-adapter/README.md) |
| Step 002 | CLI 结束后怎样取回统计与代码补丁 | [步骤记录](steps/step-002-agent-results/README.md) |
| Step 003 | 补丁怎样在独立环境中得到奖励 | [步骤记录](steps/step-003-swe-evaluation/README.md) |
| Step 004 | 轨迹与奖励怎样交成 Sample | [步骤记录](steps/step-004-trajectory-to-samples/README.md) |
| Step 005 | Adapter 服务与本次会话怎样准备 | [步骤记录](steps/step-005-agent-preparation/README.md) |
| Step 006 | 执行沙箱怎样准备、交付和回收 | [步骤记录](steps/step-006-agent-sandbox/README.md) |
| Step 007 | 已有沙箱怎样准备成题目工作区 | [步骤记录](steps/step-007-prepare-workspace/README.md) |
| Step 008 | CLI 怎样启动，结果怎样交回 | [步骤记录](steps/step-008-harness-communication/README.md) |
| Step 009 | CLI 的 HTTP 请求怎样进入 Adapter 并往返模型服务 | [步骤记录](steps/step-009-adapter-request-entry/README.md) |

外层结果状态、失败与最终清理，以及复杂轨迹和并发分支的后续边界，见[已有覆盖核对](steps/step-009-adapter-request-entry/04-flow.md#coding-agent-coverage-check)。本次主题分组仅改变存放位置，下一处实际阅读仍从[唯一路线](../../../../../slime_photo/code-reading/repo-reading-route.md#当前接续)接续。
