# Trial.__init__

- 本步调取：Step 013 从 [进入本步的完整快照](../../../../../03-long-term-memory/functions/harbor/trial/trial.py/Trial.__init__.md) 调入；沿用 Step 012 的原话与认识时间，本轮只补环境创建调用的交接。

- 本步继承：2026-11-13，由 [Step 012 来源卡片](../../../../../../step-012-task-agent-verifier/02-short-term-memory/functions/harbor/trial/trial.py/Trial.__init__.md) 完整继承；复制不改变原认识时间或已掌握状态。

- 源码：[src/harbor/trial/trial.py:164](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/trial.py#L164)，Harbor v0.25.0，固定提交 fdba28fc411e47e8765420a1a063b4918fce3def。
- 首次单独展开：Step 012，2026-11-13，由 SingleStepTrial.__init__ 的 super 调用进入。
- 最近认识更新：2026-11-13，用户已重新表述 config 为本次运行安排与来源、task 为问题具体内容，并表示理解；组件创建内部仍未展开，result 初值由助手校准。

[SingleStepTrial.__init__](../../../../../03-long-term-memory/functions/harbor/trial/single_step.py/SingleStepTrial.__init__.md) → **Trial.__init__** → 返回子类设置产物收集标记 · [scope](../../../../../01-scope.md)

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：具体 Trial 子类已经接到题目与配置，需要准备一次尝试共用的身份、记录、状态和组件。
2. **具体内容**：保存输入，准备目录与 lock 记录，初始化状态，再组织日志、超时、Agent、可选模拟用户、环境和产物处理组件的初始化及网络配置检查。
3. **建议构建的心智模型**：

   > 把“题目 + 本次运行安排”接到同一个尝试对象上，为后续 run 准备它要使用的身份、状态和组件。

4. **调用代码**（来自 SingleStepTrial.__init__）：

   ```python
   super().__init__(
       config,
       _task=_task,
       _task_download_result=_task_download_result,
   )
   ```

## 本场景的输入与输出

### 从哪里来，带着什么？

Trial.create 的单步分支调用 SingleStepTrial(...)，其初始化转入这里。self 仍是正在初始化的 SingleStepTrial 实例；config、已读的 hello-world Task 与材料记录原样进入。返回后继续子类的 _are_artifacts_collected=False，再回 Trial.create。

### 快速回忆：这里的 config 和 task 装什么？

沿用前面同一份 hello-world 静态例子，只列当前需要的字段，未执行模型或构造器：

```text
config: TrialConfig                     # 这一次尝试怎样安排？
├─ task.path: examples/tasks/hello-world # 题目从哪里来
├─ agent.name: claude-code              # 由哪个 Agent 做
├─ agent.model_name: anthropic/example-model  # 示意模型名
├─ environment.type: docker            # 用什么运行环境
├─ verifier.disable: False             # 这次启用评测
└─ trials_dir / trial_name             # 本次记录放在哪里

task: Task                             # 按来源读出来的题目是什么？
├─ instruction: 创建 hello.txt，写入 "Hello, world!"  # 中文概述原指令
├─ config: 从这道题的 task.toml 解析出的定义
├─ paths: 这道题的 instruction、environment、tests 等材料位置
└─ has_steps: False
```

config 由前面的 JobPlan 组合，task 由刚读过的 _load_task 取得。config.task 保存题目来源；task 是读取后的题目对象。task.config 是题目定义，与整个 TrialConfig 的运行安排分工不同。

当前构造器把二者放到同一次尝试上，随后创建组件：例如 Agent 创建入口会使用运行安排，后面的执行阶段会使用题目 instruction。这里的路径分两种：task.paths 指向题目材料；self.paths 指向这次尝试自己的记录目录。

**result 目前只设初值**：self._result = None；后面的 Trial.run 才调用 _init_result。此处还没有得到执行结果。当前主干可保留为“保存题目与运行安排 → 准备本次身份、记录位置和状态 → 初始化组件”。

### 核心骨架：保存材料 → 准备本次状态 → 组织组件创建

以下是正常路径的教学裁剪：保留真实签名、关键赋值与调用顺序；省略缺失 Task 的检查、skills/环境路径准备及部分内部状态字段。各 helper 暂按职责看待，不继续全部下钻。

```python
def __init__(
    self,
    config: TrialConfig,
    *,
    _task: Task | None = None,
    _task_download_result: TaskDownloadResult,
):
    # [1] 保存材料，分配这次尝试的身份。
    self.config = config
    self.job_id = config.job_id
    self._id = uuid4()
    self.task = _task
    self._task_download_result = _task_download_result

    # [2] 准备记录位置；这部分会创建本地目录并写 lock 记录。
    self.paths = TrialPaths(trial_dir=(config.trials_dir / config.trial_name))
    self.paths.mkdir()
    self._trial_lock = self._write_trial_lock()
    # 原码还准备环境路径、skills、hooks 和清理状态，本段省略。
    self._result: TrialResult | None = None

    # [3] 组织共用组件初始化。当前只读到环境创建入口。
    try:
        self._init_logger()
        self._init_timeouts()
        self._init_agent()              # 当前子卡：按配置创建主 Agent 对象。
        self._init_user_agent()
        self._init_agent_environment()  # 本步从这里进入环境创建函数卡。
        self._init_artifact_handler()    # 后续位置，只定位。
        self._validate_network_policy_modes()
    except BaseException:
        self._close_logger_handler()
        raise
```

1. **保存材料**：task 直接接住已经加载的对象；job_id 表示所属 Job，_id 是此尝试自己的 UUID。Task 身份与一次尝试的身份用途不同。
2. **准备本次状态**：本地目录按 trials_dir / trial_name 确定，lock 使用运行配置及材料记录等信息生成。_result 初始为 None，后面 Trial.run 才调用 _init_result；当前尚无执行结果。
3. **组织组件创建**：本轮先知道 Agent 和 Environment 对象由这些入口准备。_init_agent 已在[独立函数卡](../../../../../03-long-term-memory/functions/harbor/trial/trial.py/Trial._init_agent.md)展开创建接缝；具体工厂选择仍留在下游；本例 user_agent=None，可选模拟用户分支不展开。环境初始化内部交给 Step 013。

完整初始化正常结束后，对象持有 config、task、材料记录、身份与路径，以及 Agent/Environment 等共用依赖；随后子类补充自己的标记。这里的描述是源码推导的正常路径状态，没有真实运行值。构造器有创建本地目录和写记录的副作用；环境实际启动、Agent 执行与评测在后续生命周期中发生。

| 阅读位置 | 后续问题 | 返回与边界 |
| --- | --- | --- |
| self._init_agent() | [进入 Trial._init_agent 卡片](../../../../../03-long-term-memory/functions/harbor/trial/trial.py/Trial._init_agent.md)看配置到对象的交接 | 返回后继续本构造器的 _init_user_agent；具体工厂内部暂不展开 |
| self._init_agent_environment() | [本步环境创建卡](Trial._init_agent_environment.md) | 返回后继续产物组件初始化和检查，再返回 SingleStepTrial.__init__ |
| 本方法结束 | 共用准备交回单步子类 | 回到 SingleStepTrial.__init__ 设置 _are_artifacts_collected=False |



### Step 013 接续：从已有构造现场进入环境创建

沿用上述同一 config、task 和尝试身份。当前调用 self._init_agent_environment()，进入 [本步环境创建卡](Trial._init_agent_environment.md)。它将创建结果写到 self.agent_environment，返回后本构造器继续产物组件初始化与检查；基类和子类初始化完成后，才接到 Trial.create 的返回。本次调取不改变上面 Step 012 的个人认识与历史边界。


## 我的直接表述（原话）

用户本轮指定阅读 SingleStepTrial，入口原话保存在[调用方卡片](../../../../../03-long-term-memory/functions/harbor/trial/single_step.py/SingleStepTrial.__init__.md)。基类作为其 super 初始化的直接下游接入。

用户随后概括主干并反馈遗忘：

> 鸡蛋啊来说就是保存了这个是什么config和rtask
> 然后记录了位置？
> 以及trial的result？
> 然后初始化一系列的内容
> 其实我都有点快忘了这里的conifg和task 里面具体是什么了

助手按同一 hello-world 例子补回运行安排与题目内容的字段对照，并校准 _result 在此只是 None；该解释尚待反馈，不将这次概括记为已经掌握所有初始化内部。


用户随后确认已想起两份输入：

> 好的 我想起来了
> config是是 题目打算怎么运行 来源是什么 选择什么模型什么harness 什么环境是否测评
> task 就是 这个问题具体是什么
> 好的我理解了
> 那么下一个我们需要看的函数是什么呢？

这次表述已明确运行安排与题目内容的关系。下一处推荐 Trial._init_agent：围绕 config.agent 怎样交给工厂并得到 self.agent，先看创建接缝；不因推荐提前创建未读函数卡。

## 尚不清楚

- 用户此前反馈 config/task 内容模糊，经就近对照后已明确重新表述两者关系；完整字段仍按需回查，不要求背诵。

- _init_agent 已展开参数准备、工厂调用与身份设置；工厂内部如何选择具体类仍留白。
- skills、lock 完整结构、各类超时与清理状态不逐项展开。
- Environment 创建和后续产物配置检查的内部实现留到对应已确认范围。

<details>
<summary>来源、版本与验证边界</summary>

- [固定版本 Trial.__init__](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/trial.py#L164)，以及同文件的 _write_trial_lock 和 run：核对状态写入、lock 副作用与结果初始化时机。
- 当前本地源码路径不可用，本轮使用官方 v0.25.0 固定提交，未混用 main。示例沿此前 hello-world / user_agent=None 场景；没有执行构造器、写实际题目记录、启动环境或调用模型。
- [Step 012 本次过程](../../../../../../step-012-task-agent-verifier/04-flow.md#single-step-init-entry-20261113)。

</details>
