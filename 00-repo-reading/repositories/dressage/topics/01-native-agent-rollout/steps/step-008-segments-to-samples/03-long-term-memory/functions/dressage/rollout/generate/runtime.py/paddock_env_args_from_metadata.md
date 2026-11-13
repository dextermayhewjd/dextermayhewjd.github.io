> Step 008 前序继承：来自 [Step 007 的完整记录](../../../../../../../step-007-proxy-finalization-and-trajectory/03-long-term-memory/functions/dressage/rollout/generate/runtime.py/paddock_env_args_from_metadata.md)。保留原话、认识时间与未知；继承不表示本步已读或新增掌握。

# paddock_env_args_from_metadata

> Step 007 继承：来自 [Step 006 的 03-long-term-memory 记录](../../../../../../../step-006-agent-execution/03-long-term-memory/functions/dressage/rollout/generate/runtime.py/paddock_env_args_from_metadata.md)；保留原话、来源与未知，继承不表示新增掌握。

> Step 006 继承：来自 [Step 005 的 03-long-term-memory 记录](../../../../../../../step-005-agent-registration/03-long-term-memory/functions/dressage/rollout/generate/runtime.py/paddock_env_args_from_metadata.md)；保留前序原话、认识时间和未知，不表示本步新增掌握。

- 源码定位：[runtime.py:203](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/generate/runtime.py#L203)。
- 首次单独展开：Step 001，2026-11-05。
- 最近认识更新：Step 001，2026-11-06；用户提出参数筛选与统一返回的理解，助手补充配置和环境创建的边界。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：generate 准备好身份信息和 Agent 类型后，从 sample.metadata 中整理之后交给 Paddock 的环境参数。
2. **具体内容**：从固定四个字段中取出 metadata 实际具有的字段，创建 env_args 字典；再合入 extra_env_args，重名时以后者为准；返回字典。
3. **建议构建的心智模型**：

   > metadata 是本次任务携带并持续补充的信息字典。这个函数只从中选出环境配置，再合入调用者的补充参数。返回的是环境参数，不是环境本身。

4. **调用代码**（generate:142–152，连续源码）：

   ```python
   blackbox_type = normalize_blackbox_type(
       metadata.get("blackbox_type") or DEFAULT_BLACKBOX_TYPE
   )

   extra_env_args = None
   if "blackbox_type" in metadata or blackbox_type != DEFAULT_BLACKBOX_TYPE:
       extra_env_args = {"blackbox_type": blackbox_type}
   env_args = paddock_env_args_from_metadata(
       metadata,
       extra_env_args=extra_env_args,
   )
   ```

   blackbox_type 不在四个直接筛选字段中；满足上述条件时，通过 extra_env_args 加入。这里只辨认参数来源，不展开类型规范化函数。

## 本场景的输入与输出

### 调用前的交接

调用者 generate 先通过 [normalize_blackbox_type](../../../paddock/blackbox/common/defaults.py/normalize_blackbox_type.md) 取得统一格式的类型名称，再按条件放入 extra_env_args。本函数接收这份补充字典并合入 env_args；名称规范化的完整源码与解释见独立函数卡。

### 1. 先看本函数关心的 metadata

metadata 来自 sample.metadata。generate 之前已确保它是字典，清理部分错误记录并写入两个 ID。它不只保存环境配置；本轮不需要穷举所有键。

| 直接筛选的键 | 当前理解到的用途 |
| --- | --- |
| sandbox_timeout_sec | 沙箱超时配置；Paddock.init 会传入 SandboxSpec.timeout_sec |
| sandbox_image | 环境镜像或模板的选择信息；具体含义取决于 provider |
| sandbox_cmd | 交给后端处理的沙箱命令配置；这里不执行命令 |
| sandbox_extra_params | 后端附加参数；支持哪些键由具体 provider 决定 |

例如 E2B 会读取镜像/模板、命令和附加参数；不能由本函数的透传推断所有 provider 都支持相同字段。session_id、instance_id、execute_cmds 等不在这四项中。

### 2. 输入与输出对照

教学示例：采用未显式指定 blackbox_type、规范化后仍为默认类型的调用分支，因此 extra_env_args 为 None。镜像字符串只是示意，不代表验证过的可用环境。

输入：

```python
metadata = {
    "session_id": "bbs-demo",
    "instance_id": "task-7",
    "sandbox_image": "example-template",
    "sandbox_timeout_sec": 300,
    "execute_cmds": [],
}
extra_env_args = None
```

返回：

```python
env_args = {
    "sandbox_timeout_sec": 300,
    "sandbox_image": "example-template",
}
```

metadata 本身没有被这个函数改写；缺失的 sandbox_cmd 和 sandbox_extra_params 不会被补成默认值。

### 3. 完整函数和字段列表

下面两段均来自 runtime.py，中间无关代码省略。

```python
_PADDOCK_ENV_ARG_KEYS = (
    "sandbox_timeout_sec",
    "sandbox_image",
    "sandbox_cmd",
    "sandbox_extra_params",
)


def paddock_env_args_from_metadata(
    metadata: dict[str, Any],
    *,
    extra_env_args: dict[str, Any] | None = None,
) -> dict[str, Any]:
    env_args = {key: metadata[key] for key in _PADDOCK_ENV_ARG_KEYS if key in metadata}
    if extra_env_args:
        env_args.update(extra_env_args)
    return env_args
```

1. 按固定键列表筛选，存在的键才加入新字典；判断的是键存在，所以值为 None 时也会取出。
2. extra_env_args 非空时合入新字典。它可以新增列表外的键，也可以覆盖同名值；例如额外传入 sandbox_timeout_sec=600 会覆盖原来的 300。这是辅助函数的通用行为，当前 generate 的补充字段是 blackbox_type。
3. 返回 env_args。这里只新建外层字典，嵌套字典等值仍引用原对象，不是深拷贝；也不校验镜像是否可用或参数是否合法。

### 4. 返回主线

返回 generate:149，由局部变量 env_args 接住。沿预热未命中的路径，后面传给 paddock.init(traj_id=session_id, env_args=env_args)，再由 Paddock 构造 SandboxSpec；预热命中时会改用 handle.env_args。这里仅定位交接，不展开预热与 provider。

## 我的直接表述（原话）

> 好的那么这里需要专门看一下metadata到底存了什么内容吗?
> 还是什么?
> 我觉得需要先生成一个short term memroy吧
> 关于paddock env args from metadata

这是对阅读前置和记录方式的提问，尚不是对函数实现的理解确认。

2026-11-06 对实现的理解：

> 好的那么看一下这里的这个内容吧
> 我可以简单理解为这里是通过metadata来获得这里关于
> 这个和image相关的一系列内容的吗?
> 也就是通过paddock env 来构建这里和image相关的内容
> 来完成对于环境的统一的构建?
> 关于一个sandbox 要求的image是什么样子的
> 包括这里的metadata是什么
> 宗旨和一系列paddock env arg keys都列在这里的env args中
> 终然填写完整了之后通过统一第二方式返回是我的理解

助手核对：已抓住从 metadata 筛选参数、组成 env_args 并返回的方向。需要区分三点：参数涉及整个沙箱环境，image 只是其中一项；此处整理配置，不构建镜像或创建环境；仅复制已有键，不保证四项齐全，也不把整个 metadata 嵌入 env_args。随后合入 extra_env_args，同名键覆盖。上述澄清尚待用户确认。

## 尚不清楚

- 各个任务的数据入口怎样填入这四个环境字段，本轮未追踪。
- 不同 provider 具体如何使用或校验这些参数，本轮不展开。
- blackbox_type 的规范化已在独立卡展开，尚待用户对其机制表达理解确认。

<details>
<summary>来源、验证与完整例子</summary>

- 固定版本：3e3142fe8ea07e4504c3b20a936a4c201a3de44c。
- 源码：runtime.py 的 _PADDOCK_ENV_ARG_KEYS 与 paddock_env_args_from_metadata；blackbox_dispatch.py:126–152 及预热分支；paddock/blackbox/paddock.py:64 起的 init。
- 后端字段用途核对：sandbox/remote/e2b/provider.py 中的字段读取；不把 E2B 行为泛化为所有 provider。
- 示例为静态推导，没有运行环境或训练。
- [本步讨论](../../../../../../../step-001-task-identity-and-parameters/04-flow.md)。

</details>
