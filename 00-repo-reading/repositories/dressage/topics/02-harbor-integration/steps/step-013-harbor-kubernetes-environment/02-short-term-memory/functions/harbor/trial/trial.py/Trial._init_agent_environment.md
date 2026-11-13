# Trial._init_agent_environment

- 源码：[src/harbor/trial/trial.py · Trial._init_agent_environment](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/trial.py)，Harbor v0.25.0，固定提交 fdba28fc411e47e8765420a1a063b4918fce3def。
- 首次单独展开：Step 013，2026-11-13，用户确认开始本步，从前一步已定位的环境入口接续。
- 最近认识更新：2026-11-13，用户已表述按环境配置创建的主线，追问题目环境要求；助手校准为同一环境的三类输入，输出为 Environment 对象；补入旁注后用户表示差不多了解，尚无内部机制的独立复述。

[调用方 Trial.__init__](Trial.__init__.md) → **Trial._init_agent_environment** → 返回 Trial 初始化 · [本步 scope](../../../../../01-scope.md)

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：Trial 已取得题目、保存本次运行安排并创建主 Agent 对象，现在需要准备后续执行使用的环境对象。
2. **具体内容**：准备本地产物挂载目录与网络策略，将运行后端配置、题目的环境定义、记录位置和会话信息交给 EnvironmentFactory，保存返回的对象并设置 context_id；按需调整本地权限。
3. **建议构建的心智模型**：

   > 把“本次选用的环境后端”和“这道题的环境要求”交给工厂，得到这次尝试的环境对象，保存到 self.agent_environment；实际启动由后面的 start 接续。

4. **调用代码**（Trial.__init__ 内的连续位置）：

   ```python
   self._init_agent()
   self._init_user_agent()         # 当前示例 user_agent=None。
   self._init_agent_environment()  # 本步首先进入这里。
   self._init_artifact_handler()   # 当前方法返回后，继续基类其余初始化。
   ```

## 本场景的输入与输出

### 从父函数带着什么进来？

Step 012 已区分 config（本次运行安排）、task（读取后的题目）与 agent（工厂创建的对象）。当前仍处在同一个 SingleStepTrial 实例的基类初始化里，尚未调用 trial.run。

本轮先沿用 hello-world 和 Docker 作为共同入口的静态例子，读清对象创建；后面的后端合同与 Agent Sandbox 对齐继续按本步 scope 推进，不把 Docker 示例当作 K8s 已接通。

| 已有材料 | 当前调用怎样使用 |
| --- | --- |
| self.config.environment | 本次运行后端配置；例子中 type 为 docker |
| self.task.config.environment | 从题目 task.toml 读出的环境要求，整体交给工厂 |
| self.task.paths.environment_dir | 这道题的 environment/ 材料目录 |
| self.task.short_name | 环境命名使用的任务短名 |
| self.config.trial_name / self._id | 本次尝试的名称与 UUID |
| self.paths / self.logger | 本次尝试的记录路径与日志对象 |
| 挂载和网络策略输入 | 原函数还传入显式/自动挂载及阶段策略，本轮先按接口保留 |

### 三类输入共同描述一个环境

它们不是三个分别创建的环境：运行配置决定“用哪种后端”，材料目录提供“用来构建或配置环境的文件”，题目环境定义说明“这道题声明的资源与运行要求”。三者一起用于创建同一个环境对象。

| 当前参数 | hello-world 场景中的具体含义 |
| --- | --- |
| config=self.config.environment | 本次选择 Docker 后端来管理运行环境 |
| environment_dir=self.task.paths.environment_dir | 题目的 environment/ 目录；其中 Dockerfile 使用 ubuntu:24.04，并设置工作目录 /app |
| task_env_config=self.task.config.environment | 从 task.toml 的 [environment] 读取声明的要求；本例 cpus=1、memory_mb=2048、gpus=0 |

题目 [environment] 的真实字段节选：

```toml
[environment]
cpus = 1
memory_mb = 2048
gpus = 0
```

这些是题目声明的规格，不是当前机器已经提供的资源或已启动容器的测量结果。当前工厂接收这些输入并返回 Environment 对象；它并不是再生成一份配置。运行配置如何覆盖题目声明、各后端怎样落实资源规格，留到确有需要时查看工厂和具体后端。

### 核心代码：配置交给工厂，返回对象存到 Trial

以下为教学裁剪，保留真实签名、核心实参、赋值与身份设置。网络策略组装、工厂调用中的 logger/挂载/策略参数和末尾的权限分支暂时折叠，完整源码在文末；不能用这段裁剪代码替代原实现运行。

```python
def _init_agent_environment(self) -> None:
    self._prepare_artifact_mount_dirs()  # 准备宿主机上的产物目录。
    # 原码在这里计算各阶段的网络策略。

    # 下面三类输入共同描述同一个环境。
    self.agent_environment = EnvironmentFactory.create_environment_from_config(
        config=self.config.environment,              # 用什么后端？本例选择 Docker。
        environment_dir=self.task.paths.environment_dir,  # 构建材料在哪里？本例目录含 Dockerfile，使用 Ubuntu 24.04。
        environment_name=self.task.short_name,
        session_id=f"{self.config.trial_name}__env",  # 本次环境的会话名。
        trial_paths=self.paths,
        task_env_config=self.task.config.environment, # 题目要求什么规格？本例 1 CPU、2048 MB 内存、0 GPU，来自 task.toml。
        # 原调用还传 logger、mounts、auto_mounts 和网络策略，暂时折叠。
    )                                                # 返回环境对象，保存到当前 Trial；实际启动留到后面的 start。
    self.agent_environment.context_id = self._id
    # 原码随后按 auto_mounting 调整本地记录与产物目录权限。
```

1. **交出两类配置**：config.environment 描述本次使用的运行后端，task.config.environment 描述题目的环境要求；environment_dir 把题目提供的构建等材料位置一并交出。具体怎样选择实现、处理参数，由工厂负责，当前不展开它内部所有后端。
2. **保存对象**：工厂结果写入 self.agent_environment。本方法正常返回 None，主要结果是当前 Trial 上多了环境对象。
3. **关联本次尝试**：session_id 使用 trial_name 加 __env 后缀；context_id 使用父构造器生成的同一个 UUID，和前面的 Agent 对象关联到同一次尝试。

### 调用后留下什么？

以下是静态状态示意，没有运行构造器或创建容器：

```text
self: SingleStepTrial
├─ config / task / agent       已有运行安排、题目和 Agent 对象
└─ agent_environment           工厂返回的 Environment 对象
   └─ context_id               与 self._id 相同的尝试 UUID

传入工厂的 session_id：<本次 trial_name>__env
本地副作用：准备产物目录；auto_mounting 分支还会调整相关目录权限
```

当前方法里没有调用环境 start。它返回 Trial.__init__ 后，基类继续初始化产物处理组件并作检查；之后依次返回 SingleStepTrial.__init__ 与 Trial.create。队列接住 trial、挂 hooks，再调用 trial.run，才会沿 _prepare → _setup_agent_environment → _start_agent_environment 调用环境 start。这里只定位后续交接，启动函数尚未在本轮展开。

### 暂时折叠的代码各负责什么？

| 位置 | 先保留的职责 | 按什么问题再展开 |
| --- | --- | --- |
| _prepare_artifact_mount_dirs | 创建本地将用于产物挂载的目录 | 文件收集或目录权限有问题时 |
| steps 与 plans | 按题目步骤准备网络策略，覆盖不同运行阶段；重评有专门分支 | 解释联网、Agent/Verifier 网络切换或后端能力时 |
| mounts / auto_mounts | 把显式挂载与框架准备的挂载资料交给后端 | 对照后端文件、日志与挂载合同时 |
| auto_mounting 分支 | 按后端行为调整宿主机相关目录权限 | 后端挂载或权限验证时 |

## 我的直接表述（原话）

用户确认开启本步：

> 好的 那么现在开始一下这里的这个step013吧

用户随后复述并追问：

> 好的 简单来看的话
> 这里在做的内容就是根据这里这个environment config来实现生成当前需要的环境配置是我的理解
> 但是这里给出了三个不同的环境
> 也就是什么后端
> 环境材料放在哪里
> 以及这个题定义的环境要求是什么（这个我有点没理解）
>
> 不过这一个short term funciton应该就这样子了吧
> 还有什么需要继续看的吗？

助手校准：三项是同一环境的输入，输出是环境对象；用 hello-world 的 Dockerfile 与 task.toml 资源字段具体说明题目要求。用户已表达按配置创建的主线，但尚未确认这一校准，不写成已完全掌握。


用户在补入代码旁注后表示：

> 好的 我目前差不多了解了
> 那么现在继续吧
> 看一下下一个部分或者下一个function 我们需要看什么吧

此处记录为对当前讲解的大致理解与继续阅读请求，不推定已独立掌握工厂、网络或挂载内部。下一处推荐实际启动入口 Trial._setup_agent_environment，沿其委派定位 _start_agent_environment 与环境 start。

## 尚不清楚

- 用户对“题目定义的环境要求”有明确疑问；已用真实文件解释，校准尚待反馈。
- EnvironmentFactory 如何选中具体后端、怎样组合运行配置与题目要求，当前先按接口看待。
- 具体 start 怎样启动环境、判定就绪及处理超时，接下来沿本步范围进入。
- 网络策略、挂载、权限与 Agent Sandbox 的接口对应关系，后续按实际后端及问题展开。

<details>
<summary>完整源码、来源与验证边界</summary>

以下是官方固定版本中该方法的完整源码，便于回查教学裁剪部分：

```python
def _init_agent_environment(self) -> None:
    self._prepare_artifact_mount_dirs()
    steps = self.task.config.steps or [None]
    # Providers such as Modal choose their startup strategy from the planned
    # execution policies. Static environments infer a shared startup policy.
    # Regrade never starts this environment; only its separate verifier runs.
    plans = [
        self._network_plan(step, dynamic_network_policy=True)
        for step in steps
        if not self.config.is_regrade
    ]
    self.agent_environment = EnvironmentFactory.create_environment_from_config(
        config=self.config.environment,
        environment_dir=self.task.paths.environment_dir,
        environment_name=self.task.short_name,
        session_id=f"{self.config.trial_name}__env",
        trial_paths=self.paths,
        task_env_config=self.task.config.environment,
        logger=self.logger,
        mounts=self.config.environment.mounts,
        auto_mounts=self._agent_env_mounts,
        network_policy=plans[0].agent_env_baseline if plans else None,
        phase_network_policies=[
            phase
            for plan in plans
            if not self.config.install_only
            for phase in (
                [plan.agent_phase, plan.verifier_phase]
                if not self.config.verifier.disable
                and plan.verifier_env_baseline is None
                else [plan.agent_phase]
            )
        ],
    )
    self.agent_environment.context_id = self._id
    if self.agent_environment.auto_mounting:
        self.paths.chmod_dir()
        self._chmod_artifact_mount_chain()
```

- [官方固定版本 trial.py](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/trial.py)：核对当前方法、父构造器、本地产物目录准备及后续 start 调用。沿用 v0.25.0，当前按符号核对，不把网页解析后的重排行号当作原文件行号。
- 当前原本地 checkout 不可用，通过官方固定提交静态核对；未实例化真实 Environment、启动 Docker/Pod、执行安装、模型请求、集群或训练实验。后端工厂与适配器尚未在本轮展开。
- 题目要求依据官方 [hello-world/task.toml](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/examples/tasks/hello-world/task.toml)；构建材料依据 [environment/Dockerfile](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/examples/tasks/hello-world/environment/Dockerfile)。只摘取环境相关字段，未构建镜像或测量资源。
- [Step 013 本轮开始与范围](../../../../../../step-013-harbor-kubernetes-environment/04-flow.md#step013-start-20261113)。

</details>
