# 01 · Dressage Step 013：把 Harbor Environment 合同映射到已有 K8s 能力

[主题入口](../../../../README.md) · [项目进度](../../../../../../README.md) · [整体规划](../../../../../../references/topics-and-step-scopes-after-step006.md) · [前一范围](../../../step-012-task-agent-verifier/01-scope.md) · [后一范围](../../../step-014-model-routing-and-api-contract/01-scope.md)

> 状态：按已确认规划预先准备 scope；尚未据此开始逐函数阅读或实施验证。本步未创建短期、长期记忆及完成记录。

## 1. 阅读目标

**先判断 Harbor 已有 K8s 后端能复用到哪里，再明确目标 Agent Sandbox 接缝的差异；让一题的冷创建、执行、文件访问和回收形成可验证的合同。**

Harbor 锁定版本已包含 GKE、ACK、OpenShift 环境实现，不能默认从零补 K8s 支持。先看[已有后端与 Agent Sandbox 的区别](../../../../../../references/harbor-kubernetes-backends.md)；当前目标若仍要求 kubernetes-sigs/agent-sandbox 的 WarmPool/Claim，再核对这一特定 CRD 接缝。

## 2. 指挥官、入口条件与边界

1. **指挥官与入口**：[Trial 的环境准备位置](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/trial/trial.py) 用来定位调用方；核心接口是 [BaseEnvironment](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/environments/base.py#L892)。本步输出接口映射，不假定已有可直接使用的 Harbor–Agent Sandbox 实现。
2. **进入前已有**：已有一份可解释的 Task/Trial 配置。对照现有 UpstreamK8sSandbox 的直建、SDK 和 Provider 分支，首条验证路线选择冷创建；暂不假定任意分支语义相同。
3. **停止位置**：列清每个 Harbor 方法对应现有哪项能力、还缺什么，以及不支持配置如何报错。合同明确后可另行执行一题 Oracle/确定性基线验证，本页本身不是运行记录。
4. **本轮不展开**：不重写 Kubernetes 控制器，不同时实现所有环境类型。WarmPool/Claim 的内部协调继续在已有 K8s topic 阅读。

## 3. 整体位置与本步阅读

<a id="whole-flow"></a>

### 3.1 本步在 Harbor 接入主线中的位置

这是稳定的职责图，不是把所有异步回调合成同一调用栈。原生 blackbox_dispatch/Paddock/BlackboxServer 路线作为前序背景，不嵌入本图。

```python
# 关系示意，不是可执行代码；标记的是本步观察位置。
Slime 的 rollout hook
  -> generate_rollout_harbor_sync                 # 训练入口；API-only 路线不必执行这里。
       -> _run_harbor_rollout -> _run_partition
            -> plugin.on_job_start(job)          # 挂接路由配置与生命周期回调。
            -> Harbor Job.run
                 -> Trial.run                    # 一次尝试的组织者。
                      -> _prepare                # Step 013 本步：环境与 Agent 准备。
                           -> Environment.start
                                -- 目标接缝 --> K8s 适配 -> Agent Sandbox -> Pod  # 待对齐/验证。
                           -> Agent.setup        # 按配置准备所选 Agent。
                      -> _run
                           -> Agent.run          # 执行任务，并在过程中请求模型。
                           -> Verifier.verify    # 收集评测结果。
                      -> _finalize               # 清理环境并发出生命周期事件。
                           == END 事件 ==> plugin._on_end
                                            -> commit_attempt
            <- JobResult 与插件结果
            -> _bundle_samples                   # 训练路线的结果转换。
       <- Sample 组与 metrics
  <- RolloutFnTrainOutput

# Agent.run 期间的模型交互，不是等 Trial 结束才发请求：
Agent == HTTP ==> Gateway -> Dressage Proxy -> 模型服务
# 只做 API 评估时，调用方也可以从 Harbor Job 进入，不启动 Slime 训练。
```

<a id="reading-navigation"></a>

### 3.2 本步骨架与阅读顺序

上半段是 Harbor 的调用合同，下半段是现有项目能力；虚线处是待实现/验证的适配接缝，不能当作当前真实调用栈。

```python
Trial._prepare
  -> EnvironmentFactory.create_environment_from_config(...)
  -> Environment.start(force_build=...)
  -> Agent.setup / Agent.run / Verifier.verify
       -> Environment.exec(...)
       -> upload_file / upload_dir / download_file / download_dir
Trial._finalize
  -> Environment.stop(delete=...)

# 待适配的接缝：不是已经实现的类或函数。
Harbor BaseEnvironment 合同
  -- 待映射 --> UpstreamK8sSandbox.__aenter__ / __aexit__
  -- 待映射 --> UpstreamK8sSandbox.exec / write_file / read_file
  -- 待补齐 --> 单文件与目录传输、配置语义和能力声明
  -> Agent Sandbox / Kubernetes
```

<a id="reading-sequence"></a>

下表数字只表示本步阅读顺序。原始源码、调用方、子调用与返回位置分别列出；未读方法只链接源码，不预建函数卡。

| 阅读顺序与入口 | 从哪里进入 | 读到哪里停、返回哪里 |
| --- | --- | --- |
| 1. 找到环境调用方 | [Trial._prepare 与环境准备](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/trial/trial.py) | 记录环境何时创建、谁随后使用、谁最终停止；先不追 Agent 内部。 |
| 2. 类型、工厂与现有后端复用 | [EnvironmentFactory](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/environments/factory.py) → [BaseEnvironment](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/environments/base.py) | 先比较内置 GKE/ACK/OpenShift 的要求与目标集群；只选一个实现作接口对照。ACK 的 agents.kruise.io Claim 与目标 Agent Sandbox 的 CRD 不同，不能按名称当成兼容。 |
| 3. 对照已有创建和退出 | [UpstreamK8sSandbox.__aenter__/__aexit__](/home/fredkeira/projects/slime_api_data_collecting/src/agentlab/sandboxes/k8s/adapter.py:100) | 选择一个真实分支，映射镜像、namespace、Ready、资源身份与 delete 语义。 |
| 4. 对照执行与文件 | [UpstreamK8sSandbox.exec](/home/fredkeira/projects/slime_api_data_collecting/src/agentlab/sandboxes/k8s/adapter.py:174) | 逐项核对 cwd/env/user/timeout、退出码/输出、文本与字节、目录上传下载；未支持项显式列出。 |
| 5. 回到 Trial 的完整生命周期 | [BaseEnvironment start/stop](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/environments/base.py#L892) | 用一题 Oracle/确定性执行列出待验证步骤：创建→文件/命令→Verifier→删除。 |
| 6. 转入并返回 K8s 主题 | [Agent Sandbox 跨主题导航](../../../../../03-agent-sandbox/README.md)，按该项目进度接状态写回、WarmPool、Claim 与执行访问 | 对上 start/Ready/exec/stop 的资源行为后，返回本步接口映射与验证准备；冷创建基线不等于热领取已验证。 |

版本边界：Dressage 固定 Harbor 0.18.0，而既有 Agent Sandbox 示例要求不同版本且缺少引用的集成目录。不能直接复制示例类名视为可运行。现有 SDK 分支的 exec 参数传递与目录接口尤其需要实际核对。

具体核对见[当前 Agent Sandbox 与 Harbor 的兼容性记录](../../../../../../references/agent-sandbox-harbor-compatibility.md)：当前本地示例的适配实现缺失，且 Dressage 运行时会拒绝 0.25.0。先确认实现与版本，再进入最小运行验证。

**读后接续**：接口映射明确后接 Step 014 的模型与采集合同；K8s 的 WarmPool/Claim 可以在对应主题完成后带回这里。

<details>
<summary>源码版本与准备状态</summary>

- Dressage 固定提交：3e3142fe8ea07e4504c3b20a936a4c201a3de44c；本轮通过本地源码定位入口、调用与返回边界。
- Harbor 使用 0.18.0 / 527d50deb63a5d279e8c20593c18a2cbc7f61f9e；沿用[前次固定版本证据](../../../../../../references/agent-sandbox-harbor-integration-evidence.json)。本轮未找到此前临时 Harbor 源码，也未重新下载，正式逐函数阅读时先恢复并核对该版本。
- 现有项目参考 /home/fredkeira/projects/slime_api_data_collecting，登记提交 151db30d1f4533773948695f4033ebe4353521d8；接口匹配以实际分支行为为准。
- [适配研究与版本差异](../../../../../../references/agent-sandbox-harbor-integration-research.md)保留来源。相关外部文档示例不自动证明当前版本可导入或可运行。
- 本页只有预备 scope。未执行 Harbor、模型、Kubernetes 或训练实验，不把范围准备当作用户已读、已掌握或验证完成。

</details>
