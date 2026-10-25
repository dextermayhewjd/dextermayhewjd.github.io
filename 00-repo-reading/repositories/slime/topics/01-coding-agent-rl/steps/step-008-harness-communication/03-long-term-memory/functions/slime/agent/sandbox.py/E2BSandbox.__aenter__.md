# E2BSandbox.__aenter__

- 源码定位：[slime/agent/sandbox.py:281–300](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/sandbox.py#L281-L300)，由助手核对。
- 首次接触：Step 2，2026-10-21，从 `_grade_scaleswe` 的评测环境创建处进入。
- 最近认识更新：2026-10-21，用户已复述“事先收到 image，进入 async with 时申请并在远端创建 sandbox”的关系；内部创建过程继续暂作黑箱。

- 本次继承自：[Step 2 的完整记录](../../../../../../step-003-swe-evaluation/02-short-term-memory/functions/slime/agent/sandbox.py/E2BSandbox.__aenter__.md)；仅复制、补来源与重算链接，原话、认识时间和未知保留。

## LLM 整理：使用场合、具体内容与心智模型

<a id="async-with-entry"></a>

1. **使用场合**：`_grade_scaleswe` 已取得任务镜像 `image`，即将进入 `async with E2BSandbox(image) as ev`。构造器先保存配置，本方法随后申请远端沙箱，供块内的补丁应用和测试使用。

2. **具体内容**：把对象已有的镜像、规格整理为 `metadata`，连同存活时间交给 `AsyncSandbox.create`。等待创建成功后，将 SDK 对象保存到 `self._sb`，从中取出 `sandbox_id`，最后返回 `self`。

3. **建议构建的心智模型**：

   > `__aenter__` 把“已保存配置的本地对象”准备成“可以操作远端沙箱的对象”：按配置申请环境，保存返回的 SDK 对象和沙箱 ID。
   >
   > 最后返回的仍是这个 `E2BSandbox` 对象，由 `as ev` 接住，供块内的评测代码使用。

4. **调用代码**（`swe.py:269–270`，节选）：

   ```python
   async with E2BSandbox(image) as ev:
       await agent_sandbox.ensure_agent_user(ev, workdir)
   ```

## 本场景的输入与输出

承接 [_grade_scaleswe](../../../examples/coding_agent_rl/swe.py/_grade_scaleswe.md#first-environment-call) 的评测场景。以下是教学配置与状态示意，镜像名为占位值。

**输入：构造器已将这些配置保存在 `self` 中。** 本方法读取这些字段；`image` 已由前面的 `E2BSandbox(image)` 传入。

```python
# 假设 SLIME_AGENT_SANDBOX_IMAGE_METADATA_KEY=image，其余采用默认配置。
# 以下展示进入时的字段值。
self.image = "teaching/calc:v1"
self.image_metadata_key = "image"
self.size = "md"
self.timeout = 3600  # 沙箱存活时间，秒
self.rpc_retries = 6
```

`image` 是镜像标识字符串；`image_metadata_key` 指定用哪个 metadata 键把它传给兼容网关。

<a id="ev-is-same-object"></a>

**成功后的输出与状态变化：**

| 项目 | 进入前 | 成功后 |
| --- | --- | --- |
| 返回值 | — | 原对象 `self`，由 `ev` 接住 |
| `self._sb` | `None` | 用于操作远端沙箱的 SDK 对象 |
| `self.sandbox_id` | `""` | SDK 返回的沙箱 ID |
| `self.image` | `"teaching/calc:v1"` | 保留原值；其他配置也保留 |

正常创建的远端副作用是新建一份沙箱环境。`ev` 在本地保存配置、SDK 对象与 ID，环境中的文件和进程仍在远端。

**输入怎样得到上述结果（`sandbox.py:291–300`）：**

第 291–296 行先整理创建参数。按本例配置推导，局部字典 `md` 为：

```python
md = {"image": "teaching/calc:v1", "size": "md"}
```

接下来执行以下关键代码（第 298–300 行，仅将调用换行展示）：

```python
self._sb = await self._rpc_retry(
    "create",
    lambda: AsyncSandbox.create(timeout=self.timeout, metadata=md),
)
self.sandbox_id = self._sb.sandbox_id
return self
```

- **配置 → 创建请求**：本例把 `timeout=3600` 和上述 `md` 交给 SDK。`md` 只描述镜像与规格；后续的工作目录、补丁、测试命令在其他调用中使用。
- **创建结果 → `self._sb`**：`_rpc_retry` 执行这里的创建操作，并处理符合条件的重试。等待成功后，返回的 SDK 对象存入 `_sb`；这个本地对象负责与远端沙箱交互。
- **SDK 对象 → `self.sandbox_id`**：从 `_sb` 读取沙箱标识，再保存到外层对象，供后续直接访问。
- **`self` → `ev`**：`return self` 返回原来的 `E2BSandbox` 对象，`as ev` 接住它。此时才执行块内第一句 `ensure_agent_user(ev, workdir)`，继续准备评测环境。
- **失败边界**：缺少镜像键名或创建最终失败时抛出异常，缩进块不会开始执行。

## 我的直接表述（原话）

2026-10-21 对创建时机的复述：

> 好的我的理解是这里在接受的时候就有这个这个镜像长什么样子的这个image
> 然后这里的e2bsandbox是在进入的时候申请这个sandbox
> 在远端创建这个sandbox
> 这个创建的过程是时发生在这里的with 进入的这个步骤这里的 对吗？

## 尚不清楚

- SDK 与服务端怎样创建环境、重试怎样处理故障，按当前阅读边界暂作黑箱。
- `ev` 所保存的状态已有解释；后续“包含全部信息”的说法已澄清为配置、SDK 对象与 ID，尚无进一步反馈。

<details>
<summary>来源、验证与完整例子</summary>

- 固定源码同页首：`sandbox.py:183–189、281–300`；本轮只整理记录，没有新增运行。
- 已有验证使用真实 Slime 方法与替身 SDK，确认传参与对象关系；未运行真实远端沙箱，详见[验证记录](../../../../../../step-003-swe-evaluation/references/sandbox-entry.md#verification)。
- [Sandbox 基础](../../../../../../step-003-swe-evaluation/references/sandbox-entry.md#sandbox-basics) · [async with 语法](../../../../../../step-003-swe-evaluation/references/sandbox-entry.md#async-with-entry) · [实现细节](../../../../../../step-003-swe-evaluation/references/sandbox-entry.md#aenter-implementation)。
- 原始 Step 2：[完整追问](../../../../../../step-003-swe-evaluation/04-flow.md#aenter-input-output) · [本次复述](../../../../../../step-003-swe-evaluation/04-flow.md#sandbox-creation-understanding)；后续对象疑问见[格式讨论中的原话](../../../../../../../../../../../../backlog/repo-reading/2026-10-20-task-driven-cognitive-architecture/discussion.md#aenter-compact-model-boundaries)。

</details>
