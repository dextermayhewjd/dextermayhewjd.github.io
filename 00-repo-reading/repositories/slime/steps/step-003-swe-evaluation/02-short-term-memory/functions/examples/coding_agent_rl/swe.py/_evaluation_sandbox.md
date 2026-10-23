# _evaluation_sandbox

- 源码定位：[examples/coding_agent_rl/swe.py:278–287](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/swe.py#L278-L287)，由助手核对。
- 首次接触：Step 003 新版核对中定位；2026-10-23 开始独立阅读并建卡。
- 最近认识更新：2026-10-23，用户已概括通过 `trace_span` 记录进入与退出阶段；完整环境交付流程尚未逐项复述。

## LLM 整理：使用场合、具体内容与心智模型

以下由 LLM 根据使用场景、调用代码和本页的输入输出整理，作为理解参考。

1. **使用场合**：`_grade_scaleswe` 已从 `md` 取出镜像、工作目录和评测配置，在应用补丁之前，通过 `async with` 取得一个新的评测环境。另一个评分器 `_grade_swebench` 也使用这层环境管理。

2. **具体内容**：接收 `image` 和追踪上下文 `trace`，经 `create_sandbox` 取得后端对象，等待其 `__aenter__` 完成，将就绪对象交给调用方作为 `ev`。调用方结束环境内的工作后，等待同一后端对象的 `__aexit__`；创建和清理分别记录追踪阶段。

3. **建议构建的心智模型**：

   > - 为一次评测管理环境的使用期：选择后端、进入环境、交出 `ev`，使用结束后退出。
   > - 这里负责环境的交付与收尾；准备用户、应用补丁和运行评测由调用方安排。
   > - `image` 指定任务镜像，后端由工厂配置选择；`trace` 用于记录创建与清理阶段。

4. **调用代码**：

   ```python
   # _grade_scaleswe，swe.py:320–322
   async with _evaluation_sandbox(image, trace) as ev:
       with trace_span(trace or [], "evaluation_prepare", record_error=False):
           await agent_sandbox.ensure_agent_user(ev, workdir)
           # 随后继续应用补丁和评测；此处只展示交出 ev 后的第一项工作
   ```

## 本场景的输入与输出

继续使用 [_metadata_scaleswe](_metadata_scaleswe.md) 的 `calc.py` 教学场景。镜像名是占位，本页只核对接口和局部控制流，没有创建真实环境。

**输入**：调用方从任务字典取出镜像；`trace` 沿评分调用传入，本任务实际由外层传入 `base_sample`。

```python
image = md["image"]             # "teaching/calc:v1"
trace = base_sample             # 本任务已有的追踪上下文
```

工作目录、补丁、测试命令保留在 `_grade_scaleswe`，不作为本函数的参数。`create_sandbox` 另读取环境变量 `SWE_SANDBOX_PROVIDER`：未设置时选择 `SunabakoSandbox`，值为 `"e2b"` 时选择 `E2BSandbox`。两者仍使用传入的同一镜像标识。

**输出与副作用**：本函数由 `@asynccontextmanager` 装饰；调用得到异步上下文管理器，进入时交付的是 `as ev` 绑定的对象。

| 时点 | 调用方得到什么，环境发生什么 |
| --- | --- |
| 成功进入后 | `ev` 是所选后端 `__aenter__` 交出的沙箱访问对象；可继续调用 `exec`、`write_file` 等能力 |
| 使用期间 | `_grade_scaleswe` 在同一个 `ev` 上准备用户、应用补丁、运行评测；本函数暂停在 `yield ev` |
| 离开时 | 本函数继续执行 `finally`，等待后端的 `__aexit__`；没有在此生成奖励或评测结果 |

这里的 `ev` 是本地用于访问评测环境的对象，不是镜像文件本身。当前两个后端的 `__aenter__` 均返回自身；本函数保留 `sandbox` 用于最后退出，调用方使用 `ev` 操作环境。

本函数的完整实现很短，可以沿四个动作读：

```python
@asynccontextmanager
async def _evaluation_sandbox(image, trace):
    sandbox = create_sandbox(image)                                      # 1. 取得后端对象
    with trace_span(trace or [], "evaluation_sandbox_create", record_error=False):
        ev = await sandbox.__aenter__()                                  # 2. 等待环境就绪
    try:
        yield ev                                                        # 3. 交给调用方使用
    finally:
        with trace_span(trace or [], "evaluation_sandbox_cleanup", record_error=False):
            await sandbox.__aexit__(*sys.exc_info())                     # 4. 使用结束后退出
```

- **选择对象**：`create_sandbox(image)` 选择并构造具体后端对象。此处先保存访问环境所需的配置；创建环境的工作在随后进入后端时进行。
- **等待进入**：`await sandbox.__aenter__()` 成功完成后，才能继续交付 `ev`。调用方尚未在这之前执行自己的环境内代码。
- **交给调用方**：`yield ev` 让 `_grade_scaleswe` 的 `as ev` 接到对象，继续执行 `async with` 内部的语句。这里是暂时交出执行权，稍后还会回来收尾。
- **退出环境**：成功进入后，调用方正常离开或因异常离开，都会来到 `finally`。`sys.exc_info()` 提供当前异常信息，正常情况为三个 `None`；具体资源回收由后端的退出方法实现。

相对旧版，入口从直接 `async with E2BSandbox(image) as ev` 改为这层共同包装。因此本轮先看共同的交付与退出，再按需要回查具体后端；原 E2B 进入、退出方法本身没有变化。

| 需要展开时进入 | 读完回到这里，接着使用什么 |
| --- | --- |
| [create_sandbox 源码](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/sandbox.py#L8-L16) | 取得后端对象，继续调用其 `__aenter__`；这次只看选择规则 |
| [返回 `_grade_scaleswe:322`](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/swe.py#L320-L329) | 使用已经交付的 `ev` 准备用户，再应用补丁 |

## 我的直接表述（原话）

2026-10-23，用户确认接下来要核对的入口（节选）：

> 是看一下这里第grade scaleswe
> 然后在需要看一下这里的evaluation_sandbox
> 这里是有了变化吗？
> 看一下这里吧
> 接下来具体看什么内容

上述为阅读方向与版本变化的提问。随后用户表达理解（节选）：

> 我感觉就是在这里也加上了这个trace_span
> 在进入和推出的时候也记录上了的感觉

这段表述对应创建与清理的追踪部分。助手补充：本函数同时负责选取后端、进入环境、交付 `ev` 和退出，两部分职责都保留在上方模型中。完整接续见[本轮讨论](../../../../../04-flow.md#ensure-agent-user-refresh)。

## 尚不清楚

- 本轮只展开共同环境管理；Sunabako 的配置读取、实际创建与回收内部尚未作为阅读内容展开。
- `__aenter__` 若失败，尚未到本函数的 `try/finally`；失败清理需要按具体后端另查。
- 教学镜像是否可用、真实环境能否成功创建与回收，本轮未运行验证。

<details>
<summary>来源、验证与完整例子</summary>

- 固定源码：`18868a79b0b083a093798a94ed0f8cb4f71b9c14`；[_evaluation_sandbox](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/swe.py#L278-L287)、[_grade_scaleswe 的输入与调用](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/swe.py#L304-L322)、[后端工厂](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/sandbox.py#L8-L16)。
- 后端对象的配置与返回边界：[SunabakoSandbox](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/sunabako_sandbox.py#L21-L83)、[E2BSandbox](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/sandbox.py#L279-L324)。仅用于核对对象关系，未据此记为已经读懂全部后端实现。
- 版本变化见[逐函数核对](../../../../../references/scope-version-review-2026-10-23.md#3-源码变化与应更新的位置)。旧版为 `2f231865`；两个评分器的新调用由本地源码核对。
- 局部验证：执行固定源码的包装函数，以替身工厂、后端和空追踪上下文验证“进入 → 调用方使用 → 退出”的先后顺序，以及调用方抛异常时的退出与传播。未运行真实后端，也未验证追踪存储。
- 形成过程：[Step 003 · 从元数据回到评分与环境入口](../../../../../04-flow.md#evaluation-environment-entry)。

</details>
