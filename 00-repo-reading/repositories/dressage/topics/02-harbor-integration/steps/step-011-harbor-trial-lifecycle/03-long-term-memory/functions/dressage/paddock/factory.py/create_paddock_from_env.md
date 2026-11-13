> Step 011 继承：来自 [Step 010 完整记录](../../../../../../step-010-harbor-rollout-entry/03-long-term-memory/functions/dressage/paddock/factory.py/create_paddock_from_env.md)。保留原话、来源、日期及未深入边界；继承不代表本步已读。

> Step 010 跨主题继承：来自 [Step 009 完整记录](../../../../../../../../01-native-agent-rollout/steps/step-009-rollout-cleanup/03-long-term-memory/functions/dressage/paddock/factory.py/create_paddock_from_env.md)。保留既有原话、认识时间、来源与未知；不代表本步重复阅读或新增掌握。

> Step 009 前序继承：来自 [Step 008 完整记录](../../../../../../../../01-native-agent-rollout/steps/step-008-segments-to-samples/03-long-term-memory/functions/dressage/paddock/factory.py/create_paddock_from_env.md)。原话、来源、认识时间与未知继续保留；继承不表示本步已读。

> Step 008 前序继承：来自 [Step 007 的完整记录](../../../../../../../../01-native-agent-rollout/steps/step-007-proxy-finalization-and-trajectory/03-long-term-memory/functions/dressage/paddock/factory.py/create_paddock_from_env.md)。保留原话、认识时间与未知；继承不表示本步已读或新增掌握。

# create_paddock_from_env

> Step 007 继承：来自 [Step 006 的 03-long-term-memory 记录](../../../../../../../../01-native-agent-rollout/steps/step-006-agent-execution/03-long-term-memory/functions/dressage/paddock/factory.py/create_paddock_from_env.md)；保留原话、来源与未知，继承不表示新增掌握。

> Step 006 继承：来自 [Step 005 的 03-long-term-memory 记录](../../../../../../../../01-native-agent-rollout/steps/step-005-agent-registration/03-long-term-memory/functions/dressage/paddock/factory.py/create_paddock_from_env.md)；保留前序原话、认识时间和未知，不表示本步新增掌握。

[返回 get_paddock_from_env](../../rollout/generate/runtime.py/get_paddock_from_env.md) · [本步 scope](../../../../../../../../01-native-agent-rollout/steps/step-003-paddock-selection/01-scope.md#reading-navigation)

- 源码定位：[paddock/factory.py:23–47](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/paddock/factory.py#L23)。
- 首次单独展开：Step 003，2026-11-06；此前只作为对象创建处定位。
- 最近认识更新：Step 003，2026-11-06；用户理解为工厂选择特定类型、后续调用 init，助手校准返回的是实例而非类本身。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：get_paddock_from_env 没有取得缓存对象时，委托本函数创建一个 Paddock 实例。
2. **具体内容**：优先使用配置的自定义类；否则按 blackbox/whitebox 模式实例化对应类；未知模式抛异常。
3. **建议构建的心智模型**：

   > 这是一处“选类并创建对象”的入口。工厂负责创建，外层 get_paddock_from_env 负责缓存；本次环境的初始化仍由之后的 paddock.init 完成。

4. **调用代码**（当前 mode=None 的默认缓存路径，缓存为空）：

   ```python
   _PADDOCK = paddock_factory.create_paddock_from_env()
   paddock = _PADDOCK
   ```

## 本场景的输入与输出

**输入**：没有传 mode；假设未配置 DRESSAGE_PADDOCK_CLASS，DRESSAGE_PADDOCK_MODE 也未配置，其他对象构造所需配置有效。

**输出**：一个新建的 BlackboxAgentPaddock 对象。paddock_mode() 提供默认 "blackbox"；类调用会执行对象构造过程，但本函数没有调用异步的 init 方法，不返回 SandboxState。

### 完整函数（增加中文注释，执行代码不变）

```python
def create_paddock_from_env(*, mode: str | None = None) -> Paddock:
    """Create the configured paddock.

    ``DRESSAGE_PADDOCK_CLASS`` remains the explicit advanced override.  The
    default path is controlled by ``DRESSAGE_PADDOCK_MODE`` and
    ``DRESSAGE_SANDBOX_PROVIDER``.
    """

    # [1] 显式配置自定义类时，优先创建它。
    class_path = os.environ.get("DRESSAGE_PADDOCK_CLASS")
    if class_path:
        return load_object(class_path)()

    # [2] 否则取得模式：函数参数优先，其次环境配置，最后使用配置默认值。
    mode = (
        mode or os.environ.get("DRESSAGE_PADDOCK_MODE") or paddock_mode()
    ).strip().lower()
    # [3] 当前默认路径：黑盒 Agent 操作对象。
    if mode == "blackbox":
        from dressage.paddock.blackbox.paddock import BlackboxAgentPaddock

        return BlackboxAgentPaddock()
    # 另一种模式：白盒工具操作对象，本轮只辨认分支。
    if mode == "whitebox":
        from dressage.paddock.whitebox.paddock import WhiteboxToolPaddock

        return WhiteboxToolPaddock()
    # [4] 未识别的模式直接报错。
    expected = "|".join(sorted(_PUBLIC_MODES))
    raise ValueError(f"unsupported DRESSAGE_PADDOCK_MODE={mode!r}; expected {expected}")
```

### 按顺序看选择过程

1. **有自定义类配置**：load_object(class_path) 加载配置指向的对象，紧接着的 () 调用它；正常约定是配置 Paddock 类，返回其实例。这条路径优先，不再走下面的模式选择。
2. **没有自定义类**：读取 mode 参数，缺省时取环境配置或 paddock_mode() 的默认值，再去空白、转小写。这里 paddock_mode() 是配置模块中的函数。
3. **按模式创建**：blackbox 返回 BlackboxAgentPaddock()；whitebox 返回 WhiteboxToolPaddock()。这两行创建的是实例，不是返回类名字符串。
4. **返回外层**：get_paddock_from_env 将实例保存到缓存，再返回 generate；后者用这个对象调用 init。这个工厂本身没有 cache_key，也不保存缓存。

在无自定义类的正常默认路径中，可概括为：未传 mode → 默认 blackbox → 创建 BlackboxAgentPaddock → 返回外层缓存。本轮读到这里即可，不自动进入该类的全部方法。

<details>
<summary>必要的边界</summary>

- 本函数不接收 allow_whitebox_mode；当前黑盒调用是否允许普通 whitebox 配置，由外层 get_paddock_from_env 检查。
- DRESSAGE_SANDBOX_PROVIDER 并没有在本函数主体中被读取；默认 Paddock 的构造过程会选择 provider。不要把“选择 Paddock 模式”和“创建具体环境”合并成一个动作。
- 无效模式会抛 ValueError；模块加载或对象构造也可能失败，不能理解为总能返回对象。

</details>

## 我的直接表述（原话）

此前关于工厂的理解节选：

> 那么这里是不是使用了工厂模式
> 然后通过这种方法来生成这里的paddock内容?
> 是我的理解?
> 通过factory这个函数和模式
> 以及env本身

本轮请求：

> 好的那么我们先看一下这里的这个paddock factory的create paddock from env 吧

后续表述：

> 好的 我理解了
> 这里其实就是一个factory mode对吗?
> 返回一个特定的class
> 后续可以用来init?
> 是我的理解

助手校准：return BlackboxAgentPaddock() 中的括号已创建实例并执行 __init__；返回后调用 paddock.init(...) 才为会话初始化环境。若仅 return BlackboxAgentPaddock 才是返回类本身。此处区分已解释，尚待用户确认。

## 尚不清楚

- 自定义类加载的完整机制不在本轮展开。
- 具体 Paddock 构造函数内部只保留职责边界，后续按需要回查。

<details>
<summary>来源、验证与完整例子</summary>

- 固定提交：3e3142fe8ea07e4504c3b20a936a4c201a3de44c。
- factory.py:16–47；config/config.py 的 DEFAULT_PADDOCK_MODE 和 paddock_mode；runtime.py:165–200。
- 默认场景为静态推导，没有实际调用工厂、初始化环境或发网络请求。
- [本步原始讨论](../../../../../../../../01-native-agent-rollout/steps/step-003-paddock-selection/04-flow.md)。

</details>
