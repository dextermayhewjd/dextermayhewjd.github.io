# get_paddock_from_env

[本步位置](../../../../../../01-scope.md#reading-navigation) · [回到 generate](../blackbox_dispatch.py/generate.md#paddock-selection)

- 源码定位：[runtime.py:165–200](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/generate/runtime.py#L165)。
- 首次单独展开：Step 003，2026-11-06；此前在 Step 002 收尾时回查过对象边界。
- 最近认识更新：Step 003，2026-11-06；用户提出按模式与环境配置，通过工厂生成 Paddock 的理解；助手补充缓存及配置层次。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：generate 没领到预热 handle，更新会话 ID 后，需要取得一个可执行环境初始化与 Agent 操作的 Paddock 对象。
2. **具体内容**：优先返回缓存对象；没有缓存时读取配置、检查模式，再委托工厂创建并缓存对象。
3. **建议构建的心智模型**：

   > 拿到一个能调用 init、register_agent 等方法的操作对象。有现成的就复用，没有就按配置创建。这里返回的是实际 Paddock 实例，不是配置草图，也不是本次环境的 state。

4. **调用代码**（generate:221–228）：

   ```python
   paddock = get_paddock_from_env(allow_whitebox_mode=False)
   state = await maybe_await(
       paddock.init(
           session_id,
           metadata.get("env_type"),
           env_args,
       )
   )
   ```

## 本场景的输入与输出

**输入**：当前调用 allow_whitebox_mode=False，未传 mode（即 None）；假设 _PADDOCK 为空、未设置自定义类、采用 blackbox 模式，且 provider 与 Proxy 地址等必要配置有效。这是正常路径教学场景，未实际创建对象。

**输出**：工厂创建的 BlackboxAgentPaddock 实例，同时赋给模块变量 _PADDOCK。下次调用若该缓存仍存在，直接返回同一个对象。该函数不接收 session_id，也不在这里为当前会话创建沙箱。

### 缓存从哪里来（同文件第 25–26 行）

定义在函数外的模块顶部，首次加载模块时为空：

```python
_PADDOCK = None
_PADDOCK_BY_MODE: dict[tuple[str, str], Any] = {}
```

字典由下面完整函数的 `_PADDOCK_BY_MODE[cache_key] = paddock`（第 195 行）填入对象，具体变化见[两次调用的例子](#mode-cache-example)。

### 完整函数（补充中文阅读注释，执行代码不变）

当前调用没有传 mode，因此参数 **mode=None**；读取配置后，局部变量 **paddock_mode="blackbox"**。两者用途不同：前者决定缓存分支，后者参与选择具体实现。

```python
def get_paddock_from_env(
    *, allow_whitebox_mode: bool, mode: str | None = None
) -> Any:
    global _PADDOCK
    # [1] 已有对象就直接复用；这一检查优先于后面的模式分支。
    if _PADDOCK is not None:
        return _PADDOCK

    # [2] 没有缓存时读取配置；通常未指定自定义类，模式为 blackbox。
    paddock_class_path = os.environ.get("DRESSAGE_PADDOCK_CLASS")
    paddock_mode = (
        mode or os.environ.get("DRESSAGE_PADDOCK_MODE") or "blackbox"
    ).strip().lower()
    # 当前调用不允许按普通 whitebox 配置创建对象。
    if not paddock_class_path and not allow_whitebox_mode and paddock_mode == "whitebox":
        raise ValueError(
            "blackbox_dispatch does not support whitebox mode; set "
            "DRESSAGE_PADDOCK_MODE=blackbox for this rollout hook, or use "
            "the Paddock API for whitebox tool execution"
        )

    from dressage.paddock import factory as paddock_factory

    # [3] 当前 generate 没传 mode，因此首次创建走这个分支。
    if mode is None:
        # 默认黑盒配置下，工厂创建 BlackboxAgentPaddock 实例并缓存。
        _PADDOCK = paddock_factory.create_paddock_from_env()
        paddock = _PADDOCK
    else:
        # 其他调用显式传 mode 时：按“自定义类路径 + 模式”分别缓存。
        # 当前 generate 不走这里；没有自定义类时，元组第一项是空字符串。
        cache_key = (paddock_class_path or "", paddock_mode)
        paddock = _PADDOCK_BY_MODE.get(cache_key)
        if paddock is None:
            paddock = paddock_factory.create_paddock_from_env(mode=paddock_mode)
            _PADDOCK_BY_MODE[cache_key] = paddock
    if paddock_class_path:
        logger.info("initialized paddock class override: %s", paddock_class_path)
    else:
        logger.info("initialized paddock from mode/provider env: %s", type(paddock).__name__)
    # [4] 返回操作对象；本次环境的 state 由后续 paddock.init 产生。
    return paddock
```

### 当前默认路径与缓存

1. **第一次调用，_PADDOCK 为空**：读取配置，因 mode=None 进入上面的 [3]；默认黑盒配置下创建 BlackboxAgentPaddock，并存入 _PADDOCK。
2. **后续调用，_PADDOCK 已有值**：直接从 [1] 返回同一个实例，不再反复创建 provider、客户端及管理字典。
3. **复用的是操作对象**：Paddock 可以按不同 trajectory_id 管理不同环境。复用它不表示不同任务共享同一个沙箱；这也不是 PrewarmStore 中预热环境的缓存。

<a id="mode-cache-example"></a>

### 例子：显式 mode 的两次调用，字典里有什么

这是补充场景，调用方式来自 whitebox_agent.py:210；主线 generate 未传 mode，不走这个分支。假设模块刚加载，_PADDOCK=None、_PADDOCK_BY_MODE={}，没有配置 DRESSAGE_PADDOCK_CLASS，其他构造条件有效，两次调用之间不改缓存或配置。

```python
# 第一次：空字典查不到，工厂创建对象并写入缓存。
paddock_1 = get_paddock_from_env(
    allow_whitebox_mode=True, mode="whitebox"
)

# 第二次：相同的键已经存在，直接返回缓存对象。
paddock_2 = get_paddock_from_env(
    allow_whitebox_mode=True, mode="whitebox"
)

paddock_2 is paddock_1  # True：是同一个实例。
```

下面用 paddock_1 表示第一次返回的 WhiteboxToolPaddock 实例。表中是符号化的状态示意，不是 Python 实际打印的对象文本。

| 时刻 | _PADDOCK_BY_MODE 的内容 | 返回什么 |
| --- | --- | --- |
| 调用前 | `{}` | 尚未调用 |
| 第一次调用后 | `{("", "whitebox"): paddock_1}` | 刚创建的 paddock_1 |
| 第二次调用后 | `{("", "whitebox"): paddock_1}` | 仍是 paddock_1，paddock_2 指向它 |

和完整函数对照：

1. **组成键（191 行）**：cache_key=(paddock_class_path or "", paddock_mode)，本例是 ("", "whitebox")。第一项是自定义类路径，未配置时为空字符串；第二项是模式。
2. **查找（192 行）**：第一次得到 None，第二次得到已有对象。
3. **创建并写入（194–195 行）**：只有第一次执行；字典是在这里填入对象的，不是在 Paddock.__init__ 中填入。

这一分支只写 _PADDOCK_BY_MODE，所以上例中的 _PADDOCK 一直为 None。显式传 "blackbox" 时会用另一键 ("", "blackbox")；不是按 session_id 缓存环境。以上为静态推导，没有实际运行工厂或创建环境。

<a id="blackbox-cache-example"></a>

### 补充例子：blackbox 也可以显式指定

继续上面的教学场景，_PADDOCK 仍为 None、没有自定义类，其他构造条件有效：

```python
paddock_black = get_paddock_from_env(
    allow_whitebox_mode=False, mode="blackbox"
)

_PADDOCK_BY_MODE[("", "blackbox")] is paddock_black  # True
```

这次创建 BlackboxAgentPaddock，并存入 ("", "blackbox")；前面 ("", "whitebox") 对应的对象仍保留。再调用相同 blackbox 参数就复用 paddock_black。此例是显式 mode 分支的静态示意；当前 generate 的真实调用没有传 mode，走 _PADDOCK 默认缓存路径。

**Claude Code / Codex 在哪一层选择？** 两者都可由 BlackboxAgentPaddock 对接，区别在后续注册参数：

| 配置 | 含义 |
| --- | --- |
| paddock_mode="blackbox" | 创建支持注册、调用 Agent 的 Paddock |
| blackbox_type="claude_code" | 注册时选择 ClaudeCodeAdapter |
| blackbox_type="codex" | 注册时选择 CodexAdapter |

若这里说 Anthropic 指 Claude Code，实际后端键是 claude_code；当前后端工厂没有名为 anthropic 的分支。blackbox_type 不进入此处的 cache_key，也不是在这里选择模型 API 协议。注册调用位于 generate:233 起，适配器选择见 blackbox_server/adapters/factory.py 的 create_adapter；本轮只定位层次，不展开注册实现。

<details>
<summary>保留的分支边界</summary>

- _PADDOCK 一旦已有值会先返回，显式 mode 也不会绕过这个早返回；不能把两种缓存理解成互不影响的完整隔离机制。
- 没有自定义类、不允许白盒且模式为 whitebox 时抛 ValueError。自定义类路径交给工厂动态加载，不在这里重新校验所有能力。
- 当前缓存键不包括 session_id、镜像或 provider；它缓存的是操作对象，不是每次任务的环境实例。

</details>

**当前下钻**：[create_paddock_from_env](../../../paddock/factory.py/create_paddock_from_env.md) 已独立建卡。看清模式如何选类并返回实例，再回到本函数的缓存与 return；不自动展开所有类和 provider。

### paddock_mode 决定哪种交互方式

| 模式 | 上层怎样使用 | 默认工厂创建什么 |
| --- | --- | --- |
| blackbox | 注册并调用一个 Agent，由 Agent 组织模型与工具交互 | BlackboxAgentPaddock |
| whitebox | 上层自己组织执行流程，通过 tool_call 逐次调用环境工具 | WhiteboxToolPaddock |

paddock_mode 不是训练/推理模式，也不是模型名称。它选择 Paddock 提供的交互接口；blackbox_type 则进一步选择黑盒里的 Agent 后端，如 claude_code、codex、opencode。blackbox 不表示无法记录轨迹，模型请求仍可以经过 Proxy。

当前 blackbox_dispatch 使用黑盒交互，注册 Agent 后再 call_agent；因此本次获取对象时传 allow_whitebox_mode=False。先理解黑盒路径即可，白盒只作区别，不新增另一条阅读主线。

### 返回的 Paddock 究竟是什么

当前黑盒实现是一个操作协调对象，把下面几项放在一起，向 generate 提供 init、register_agent、call_agent、terminate 等方法。

| 成员 | 负责什么 |
| --- | --- |
| _provider | 提供环境创建/取得、释放等能力；具体环境在调用 init 时取得 |
| _client | BlackboxServerClient，调用环境里统一的 BlackboxServer 接口，不是在这里选择 Anthropic/Codex 通信协议 |
| _proxy_public_url | 供后续注册使用的 Dressage Proxy 目标地址，要求沙箱可访问；不是每个沙箱自身的地址，也不是任意网络请求都必须使用的地址 |
| _leases、_states | 以 trajectory_id 保存该 Paddock 实例管理的环境记录与访问资料 |

Claude Code/Codex 等 Agent 后端由后续 register_agent 的 blackbox_type 参数指定，再交给 BlackboxServer 选择适配器。创建 BlackboxAgentPaddock 并不等于已经选择并启动某个具体 Agent。

paddock 是“怎么操作”的对象；state 是“这一次操作哪个环境”的资料。Paddock 协调操作，但模型请求不是每次都经由这个 Python 对象转发。缓存复用 Paddock 也不代表所有任务共用一个沙箱或绑定同一种 Agent。

## 我的直接表述（原话）

进入本步前的表述与疑问：

> 好的 我的理解是 当前看的内容就是这里else的部分
> 如果没有遇到预热的分支的话应该考虑怎么做是我的理解
> 也就需要通过get paddock from env来考虑这里的paddock应该怎么生成是我的理解
> 或者这里暂时拿到的只是这里的paddock应该长什么样子?
> 但还不是最后的具体的state?
> 到底哪一个更加偏向于harness本身呢?
> 我不是特别理解

本轮明确请求：

> 好的那么看一下这里的这个get paddock from env吧
> 单独开一个short term memory吧

助手校准：返回的是实际操作对象，可来自缓存；state 来自后续 init。这些实现说明尚待用户反馈。

本轮对创建方式的表述：

> 那么这里是不是使用了工厂模式
> 然后通过这种方法来生成这里的paddock内容?
> 是我的理解?
> 通过factory这个函数和模式
> 以及env本身
>
> 你觉得我有需要读明白的内容吗?
> 或者额外的函数?

助手确认这是按配置选择具体类并实例化的工厂方式。factory 是模块，实际函数为 create_paddock_from_env；get_paddock_from_env 额外承担缓存复用。env 指进程环境变量，mode 的 blackbox/whitebox 区别于 blackbox_type 的 claude_code/opencode 等 Agent 类型。

本轮关于模式的疑问：

> 那么这里的这个paddock mode又是什么呢?
> 没有特别明白

助手已对照黑盒注册/调用 Agent 与白盒 tool_call 接口补充说明；随后用户表示“好的 我清楚了”，并继续询问默认路径和缓存。

本轮关于默认路径和缓存的提问：

> 好的 我清楚了
> 这里是否需要在这里的完整函数里ian写一下方便我理解?
> 以偶极我想要知道的这里的默认路径是什么
> 以及这里的cache key是否我是需要理解的呢?
> 我有点没明白为什么还会有cache的路径

用户确认前面的模式说明；缓存动机和分支关系由助手在完整函数旁补充，尚待反馈。

本轮对另一缓存分支的提问：

> 好的
> 那么我们目前是否需要单独再看一下这里的显示传输的mode?
> 或者说如果是这里cache key是什么样子的呢?

已补显式 mode 的调用与元组键例子，未进入白盒执行流程；尚待用户对该分支表达理解。

本轮对返回对象组成的疑问：

> 也就是这样子的话会单独返回一个paddock?
> 但是这个paddock到底什么我其实不是特别清楚
> 我可以理解为
> 这个paddock类似于
> 集合了
> sandbox是谁提供的
> 以及内部的传输协议或者种类是什么
> 也就是是codex的server还是claude的server?
> 这里的proxy public我可以理解
> 是每一个sandbox发送的url请求?
>
> 也就是说这里的paddock应该是一种中转商或者集中管理的一种抽象?
> 结成了具体的沙箱和具体是anthropic还是codex的意思?

助手将其定位为操作协调对象，并区分 provider、BlackboxServer 客户端、代理目标地址及按轨迹保存的资料；Agent 类型在后续注册时指定。此校准尚待用户确认。

本轮关于缓存定义位置的追问：

> 但是我在这里的开头并没有看到对应的内容啊
> 我没有看到具体的paddock by mode这个字典里面有什么内容
> 还是说这里在生成的过程中是有单独在哪里被init 添加的吗?

助手补齐同文件模块级定义与第 195 行写入位置：初始为空，不是另一个 __init__ 隐式预填。

## 尚不清楚

- 用户对“已有实例”和“本次环境资料”的区分尚待进一步确认。
- 未命中后的会话 ID 更新是调用前段落，本轮未单独展开其动机。
- 自定义类加载及所有 provider 的内部实现不在本轮展开。

<details>
<summary>来源、验证与完整例子</summary>

- 固定提交：3e3142fe8ea07e4504c3b20a936a4c201a3de44c。
- runtime.py:165–200；paddock/factory.py:23 起；paddock/blackbox/paddock.py 的 __init__/init。
- 示例为静态正常路径说明；未调用工厂、未创建环境或发网络请求。
- [Step 003 本轮过程](../../../../../../04-flow.md)；[Step 002 原始边界讨论](../../../../../../../step-002-proxy-client-and-prewarm-claim/04-flow.md)。

</details>
