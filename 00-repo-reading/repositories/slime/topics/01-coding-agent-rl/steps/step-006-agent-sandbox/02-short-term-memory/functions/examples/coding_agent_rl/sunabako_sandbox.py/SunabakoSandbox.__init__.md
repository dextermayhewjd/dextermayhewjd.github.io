# SunabakoSandbox.__init__

- 源码定位：[examples/coding_agent_rl/sunabako_sandbox.py:21–27](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/sunabako_sandbox.py#L21-L27)。
- 首次接触：Step 006，2026-10-24，从 `create_sandbox(image)` 的默认分支进入。
- 最近认识更新：2026-10-24，用户概括本方法主要准备字段，并提到构造时的实例；本地实例与执行环境的边界由助手补清。

[父函数：boot_agent_sandbox](../generate.py/boot_agent_sandbox.md#boot-single-scenario) · [下一段：__aenter__](SunabakoSandbox.__aenter__.md)

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：工厂选中 Sunabako 后，构造供本次任务使用的本地操作对象。
2. **具体内容**：保存镜像标识，给沙箱编号、SDK 操作对象、命令记录、工作目录和运行方式设置初始值。
3. **建议构建的心智模型**：

   > 先给本地对象备好字段；执行环境的创建留给 `__aenter__`。

4. **调用代码**（工厂分支与父函数的相邻调用，省略其他分支）：

   ```python
   # create_sandbox(image) 选中 Sunabako 时：
   return SunabakoSandbox(image)
   # 返回 boot_agent_sandbox 后，由 cand 接住，再 await cand.__aenter__()
   ```

## 本场景的输入与输出

沿用父函数的教学镜像 `image="example-image"`，始终跟踪同一个 `cand`。

- **输入**：镜像标识字符串 `image`。
- **构造结果**：`SunabakoSandbox(image)` 得到本地实例，由工厂交回 `cand`；`__init__` 方法本身返回 `None`。
- **此时状态**：尚未调用 SDK 创建环境，`_sandbox` 为 `None`。

以下是完整方法，仅添加注释：

```python
def __init__(self, image: str) -> None:
    self.image = image                 # 之后按此标识查找镜像配置
    self.sandbox_id = ""               # 进入成功后再填写实际编号
    self._sandbox = None              # 进入成功后再保存 SDK 操作对象
    self._commands: list[dict] = []    # 后续 exec 累积命令与执行结果
    self._workdir = "/testbed"         # 默认工作目录路径，进入时可由配置覆盖
    self._runtime = None              # 进入成功后记录实际采用的运行方式
```

这里的 `self` 就是正在初始化的对象；工厂返回后，父函数用 `cand` 指向它。`_workdir` 此时只是一个字符串，赋值没有创建目录或切换执行位置。下一步在 [`__aenter__`](SunabakoSandbox.__aenter__.md) 中重点看 `_sandbox` 从 `None` 变成什么。

## 我的直接表述（原话）

2026-10-24，三个方法连读后的表述节选：

> 反正第一个更多的就是准备字段我可以这么理解
> 1.一个在创建的时候就生效的这样的一个instance

完整原话及本地实例与执行环境的边界澄清见[本轮反馈](../../../../../04-flow.md#sunabako-lifecycle-restatement)。此前[范围确认](../../../../../04-flow.md#sunabako-lifecycle-methods)保留。

## 尚不清楚

- 字段在命令执行、产物保存和运行方式判断中的完整用法，本轮只定位职责，尚未逐项深入。

<details>
<summary>源码与验证范围</summary>

- 固定版本 `18868a79b0b083a093798a94ed0f8cb4f71b9c14`；[工厂分支](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/sandbox.py#L8-L16)。
- 六个实例字段按静态源码核对；镜像名为教学构造，本轮没有创建真实环境。
- [本次连读记录](../../../../../04-flow.md#sunabako-lifecycle-methods)。

</details>
