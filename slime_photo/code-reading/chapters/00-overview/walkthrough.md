# 全局职责：从一个任务定位每个模块

[本章入口](README.md) · [阅读路线](../../repo-reading-route.md) · [入口核对清单](../../source-map.json)

源码基准：`22a89f96835969a47055a659c588f46151f8b07a`。本篇为静态源码讲解；没有运行模型、Agent CLI、沙箱、训练或集群。

## 第一眼先看什么

从一个代码任务进入：输入题目与仓库信息，启动 Agent，在执行环境中修改代码，收集 diff，在独立环境中评估，得到评分和可导出的训练轨迹。然后观察这个任务怎样被放入批量生成与训练循环。

这条阅读主线先给任务一个具体形状，再把每个模块放到相应交接上。第一遍只需要能指出责任和入口，暂时不逐行阅读全部实现。

## 每个部分具体做什么

以下路径相对于源码仓库根目录 `/home/fredkeira/projects/slime`。

| 部分 | 做什么 | 主要交接 | 第一遍找哪里 | 后续单元 |
| --- | --- | --- | --- | --- |
| `examples/coding_agent_rl/` | 将通用组件组装成代码任务，准备题目、工作区、补丁与独立评估 | 输入 `Sample` 与任务元数据；训练模式返回样本片段，评测模式返回评分结果样本 | `generate.py::generate`、`swe.py::run_evaluation` | 01、03 |
| `agent/harness/` | 安装和配置 CLI，准备模型入口与会话身份，启动并等待 Agent | `Sandbox`、工作目录、配置与 prompt → CLI 进程及退出码 | `BaseHarness.run`、两个具体 Harness | 01 |
| `agent/sandbox.py` | 提供环境创建/释放、命令、文件与长命令等待操作 | 上层 Harness/SWE 调用合同 → E2B 实现 | `Sandbox`、`exec_and_wait` | 01、06 |
| `agent/adapters/` | 接收 CLI 模型请求，转换协议消息与工具定义，调用模型并返回兼容响应 | HTTP 请求与 Session → 模型生成 → 协议响应与本轮记录 | `BaseAdapter._run_turn`、`call_sglang_generate` | 02 |
| `agent/parsing.py`、`trajectory.py` | 解析模型输出，记录多轮上下文与采样，导出训练样本 | token 与消息分支 → 工具调用表示、`TurnRecord`、带 mask/logprob 的 `Sample` | `parse_model_output`、`TrajectoryManager` | 02 |
| `rollout/` | 组织单样本/组/批次生成、评分、过滤、评测与异步收集 | 数据源与生成策略 → 已评分的样本组、批次输出或数据引用 | `generate_and_rm`、`generate_rollout_async`、`base_types.py` | 03、05 |
| `utils/eval_config.py`、`rollout/rm_hub/` | 定义评测数据集和采样配置，分发本地或远端评分 | 数据字段/样本 → 评测调用与 reward | `EvalDatasetConfig`、`async_rm` | 03 |
| `data/` | 处理数据源、任务队列、结果传输与归档、批次组织和恢复计划 | prompt/任务身份 → 生成结果/数据引用 → 训练批次与数据进度 | `data_source.py`、`queue_data_source.py`、`transport.py`、`checkpoint.py` | 05、07 |
| `observability/` | 组织日志、实验跟踪、Trace、指标和数据调试信息 | 跨调用身份与事件 → 可关联的记录与统计 | `trace_utils.py`、`logging_utils.py`、`metric_utils.py` | 04 |
| `ray/` | 分配进程/GPU 资源，组装训练与生成服务，协调批次与服务控制 | 配置与资源布局 → actor、RolloutManager 与训练消费 | `placement_group.py`、`rollout.py` | 06、07 |
| `ray/serving.py`、`backends/sglang_utils/`、`utils/health_monitor.py` | 管理模型服务状态、部署、路由、健康恢复和相关引擎操作 | ServingCluster 持有服务与队列，RolloutManager 借用引擎并组织批次 | `ServingCluster`、`deployment.py`、`external.py`、健康检查入口 | 06 |
| `backends/megatron_utils/` | 将生成数据用于训练，计算相关统计/损失，保存并发布模型状态 | token、mask、reward 等 → 训练更新、checkpoint、推理权重 | `actor.py::train_actor`、`update_weights` | 07 |
| `utils/` 的其他文件 | 提供配置、动态加载、HTTP、并发、清理与数据辅助能力 | 各主链调用需要的共用合同 | 只在主链碰到时进入 `arguments.py`、`async_utils.py`、`cleanup.py` 等 | 03–07 |
| `slime_plugins/` | 补充模型适配及独立 Rollout Buffer 等扩展 | 与原生主链或外部 Agent 框架连接的特定接口 | 第一遍只辨认 `models/` 与 `rollout_buffer/` 不同职责 | 05 对照；模型细节后置 |
| `tests/`、`.github/` | 验证组件、插件合同、恢复行为和训练/推理集成，组织 CI | fake/fixture 或实际环境 → 行为断言与回归证据 | `tests/test_agent/`、`plugin_contracts/`、相关恢复测试 | 04、05 |
| `tools/`、`scripts/`、`docker/`、`docs/` | 提供轨迹查看、模型转换、启动配置、镜像依赖和使用/开发材料 | 配置与产物 → 启动、分析、部署和维护入口 | Trace Viewer、示例启动脚本、镜像与复现文档 | 04、06、07 |

不要把目录名直接当成运行中的独立服务。一个进程可以组合多个 Python 模块；实际进程、HTTP 服务、Ray actor 与沙箱边界要沿启动代码核对。

## 三种粒度分别看

| 粒度 | 组织入口 | 负责什么 | 包含关系 |
| --- | --- | --- | --- |
| 一次 Agent 任务 | `examples/coding_agent_rl/generate.py::generate` | 环境、Agent 启动、工作产物、独立评分、样本导出与清理 | 包含 CLI 的多轮工作与多次模型请求 |
| 一次模型请求 | `BaseAdapter._run_turn` | 消息转换、模板编码、模型生成、响应与本轮轨迹 | 属于一个 Session；单轮结束不代表任务结束 |
| 一次训练迭代 | `train.py::train` | 获取 rollout 数据，训练、确认数据进度、保存与更新权重 | 可以消费多个任务，并与持续生成中的任务协调 |

一个任务可以包含多次模型请求；上下文变化或分支还可能将一份任务轨迹导出为多份训练 Sample。按任务统计结果、按请求统计延迟、按训练片段计算损失，三者需要明确关联身份。

## 沿一个代码任务读骨架

先打开 `generate.py::generate`，把实际调用按职责压缩成下面的阅读骨架。它是源码的职责摘要，不是可以直接执行的替代实现。

```text
generate(args, base_sample, sampling_params, evaluation)
  prepare adapter + task metadata
  open_session(session_id)
  with task timeout:
    with agent sandbox:
      prepare_workspace(...)
      Harness.run(...)          -> exit_code
      git_diff(...)             -> diff_text
    run_evaluation(diff_text)   -> reward
    if evaluation:
      return evaluation result
    finish_session(...)        -> training samples
    return samples
  on timeout/error:
    return aborted result
  finally:
    drop_session(...)
```

`Harness.run()` 等待期间，CLI 已在沙箱中工作，可以多次请求模型并执行工具。Slime 启动 CLI 的命令执行链与 CLI 内部的工具循环是两个边界。模型请求经 Adapter 的协议入口进入共享流程，实际生成交给 SGLang。

Agent 工作环境退出后，SWE 评分在新的评估环境中应用 diff 并运行测试。`exit_code` 描述 CLI 进程状态，reward 描述题目评测结果；不能将二者当成同一个成功标记。训练分支随后导出轨迹，评测分支返回评测结果样本，最终清理 Session。

再到 `rollout/sglang_rollout.py::generate_and_rm`，只定位 custom generate 如何加载并等待、hook 在哪里执行、group_rm 与样本评分在哪里分开、返回 Sample 或列表如何交回上层。

最后扫 `train.py::main` 与 `train`：外层先准备服务和资源，训练循环接收 rollout 数据，然后训练、记录数据进度、checkpoint、暂停相关生成并更新权重，再进入下一轮。具体恢复与权重实现留在 05、07。

固定来源：[任务组装](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/examples/coding_agent_rl/generate.py#L182)、[共享模型请求](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/adapters/common.py#L318)、[单样本生成接入](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/rollout/sglang_rollout.py#L289)、[训练入口](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/train.py)。

## 看到需求时先定位哪层

| 需求 | 首先进入 | 要保持的边界 |
| --- | --- | --- |
| 换 Agent CLI 或执行环境 | Harness / Sandbox | 配置、命令、文件、超时、取消、回连与清理语义 |
| 增加模型协议、工具格式或上下文处理 | Adapter / parsing / trajectory | 响应兼容与真实 token 轨迹；解析工具和执行工具分别定位 |
| 新增策略、环境交互或评分方法 | custom generate / RM / hooks / eval config | 输入输出、任务身份、样本扇出、分组与评测配置 |
| 任务慢、积压、重复执行或重启丢结果 | rollout / data / ray/serving.py，结合 Trace 与恢复测试 | 并发、租约、结果接受、数据消费与 checkpoint 状态 |
| 引入新训练流程 | Sample → actor/loss → 权重与 checkpoint | 生成时数据、训练时计算、策略版本与模型服务协调 |

下一步进入 [01 完整任务、Harness 与执行环境](../01-task-execution/README.md)。如果只做第一遍职责速览，按路线继续浏览各章问题与部件表即可。
