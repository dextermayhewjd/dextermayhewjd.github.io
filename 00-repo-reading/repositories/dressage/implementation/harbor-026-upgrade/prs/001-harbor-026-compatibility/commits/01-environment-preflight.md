# C01 · 让 Harbor 0.26 的环境工厂继续调用 Dressage 预检

**本笔决策**　Dressage 接收工厂传来的 `kwargs`，先交给 Harbor 基类解析，再开始本机的 bwrap 预检。

修前 `3e3142f` · Harbor 0.26.0 · 已推送 `8827b11`。六例预检通过（五例行为回归、一例上游签名快照）。

## ① 上游约定 · 环境工厂会传入 `kwargs`

DAPO 的 bwrap 示例有两次交接。**第一次由 Dressage 调用 Harbor。** Dressage 的 `_job_payload()` 生成 Job 配置，启动脚本把它交给 `harbor run --config ...`。下面节选生成的 `job.json`，这行指定本次任务由谁提供运行环境。

```json
{"environment": {"import_path": "dressage.integrations.harbor.environment:DressageEnvironment"}}
```

**第二次由 Harbor 调用 Dressage。** Harbor 的 CLI 把这个路径交给环境工厂。工厂按冒号左侧导入模块，从中取出右侧的类，所以接下来的 `env_class` 就是 Dressage 写的 `DressageEnvironment`。这个类继承 Harbor 的 `BaseEnvironment`，自己实现了预检、启动和停止。C01 发生在 Trial 入队前，工厂先在**类**上调用预检。

```python
env_class.preflight()               # 0.18 调 Dressage 的无参预检
env_class.preflight(kwargs=kwargs)  # 0.26 调同一个后端，DAPO 的默认 CLI 配置在这里传 {}
```

## ② 修前表现 · 工厂找到后端，预检却没有开始

要复现这个问题，可以直接调用工厂并省略选项。此时工厂把自己的默认值 `None` 作为 `kwargs` 传给后端。它和 CLI 传 `{}` 会触发同一个旧签名错误。

```python
EnvironmentFactory.run_preflight(
    type=None,
    import_path="dressage.integrations.harbor.environment:DressageEnvironment",
)
```

**预期**　工厂找到后端，Dressage 开始读取 bwrap 配置，检查这台机器能否运行沙箱。

**基线实测**　Harbor 0.26.0 搭配 Dressage `3e3142f` 时，调用抛出 `TypeError: DressageEnvironment.preflight() got an unexpected keyword argument 'kwargs'`。后端连读取配置这一步都没走到。

## ③ 原因定位 · 子类方法接不住具名参数

```python
env_class.preflight(kwargs=kwargs)  # Harbor 传来一个具名参数，即使它的值是 None

@classmethod                        # Dressage 基线的接收方
def preflight(cls) -> None:         # cls 由 Python 绑定，签名中没有 kwargs
```

Python 在进入方法体前就要把实参和形参对上。这里失败在参数绑定，所以即使机器上 bwrap 配置正确，工厂也走不到那项检查。原有测试直接执行 `DressageEnvironment.preflight()`，恰好省略了触发故障的关键字，修前仍然通过。

## ④ 修复决策 · 接收选项，保留原有 bwrap 检查

正式提交改了 `dressage/integrations/harbor/environment.py` 的接收方。下面是关键 diff。

```diff
     @classmethod
-    def preflight(cls) -> None:
+    def preflight(cls, kwargs: dict[str, Any] | None = None) -> None:
+        super().preflight(kwargs)
         if sys.platform != "linux":
```

- **接收选项，也保住原有无参入口。** 新签名接受工厂发来的 `kwargs`。默认值 `= None` 让直接调用 `DressageEnvironment.preflight()` 的代码也能继续执行。
- **先转交原值，再执行原有后端检查。** Harbor 0.26 要求覆盖方法调用基类，由基类执行 `cls.parse_options(kwargs)`。**临时副本实测**只改签名时，三组输入都走到了 bwrap 配置读取，但解析调用次数都是 0。这就是第二行也要改的理由。

<a id="preflight-tests"></a>

## ⑤ 回归验证 · 从真实工厂进入，检查选项和后端预检

### 5.1 旧测试检查 bwrap 命令，漏了工厂传参

```python
environment_module.DressageEnvironment.preflight()             # 测试直接无参调用后端
assert _contains(commands[0], ["--ro-bind", "/proc", "/proc"])  # 检查 /proc 以只读方式挂载
```

旧签名能接住这次无参调用，所以即使 Harbor 0.26 的工厂已经调不动后端，这一例仍然通过。

<a id="factory-preflight-cases"></a>

### 5.2 集成测试怎样验证调用兼容性？

**验证方法 · 实际调用并检查效果。** 让 Harbor 工厂按当前版本的规则调用 Dressage 的 `preflight`。如果后端签名接不住工厂传来的关键字，Python 在进入方法体前就抛出 `TypeError`。能进入后，再断言基类收到选项原值、后端开始预检。C01 据此判断兼容性，测试代码没有逐项比较新旧签名。

**用例组织 · 参数化。** pytest 每次取下面一组 `factory_arguments`，执行同一个测试函数。四组输入各有一个结果。

```python
@pytest.mark.parametrize("factory_arguments", [
    {},                                   # 第 1 次：调用工厂时省略 kwargs，工厂默认取 None
    {"kwargs": None},                     # 第 2 次：显式传 kwargs=None
    {"kwargs": {}},                       # 第 3 次：显式传空选项字典
    {"kwargs": {"test_marker": "keep"}},  # 第 4 次：传非空选项，能发现内容被清空
])
def test_preflight_through_harbor_factory(factory_arguments, monkeypatch):
    # 节选，省略用例名称和测试准备
    with pytest.raises(BackendCheckReached):  # 测试在首次读 bwrap 配置时主动停下
        EnvironmentFactory.run_preflight(
            type=None,
            import_path="dressage.integrations.harbor.environment:DressageEnvironment",
            **factory_arguments,             # 只展开本次取到的那一行
        )
    parse_options.assert_called_once_with(factory_arguments.get("kwargs"))
    backend_check.assert_called_once_with()
```

四次都问同样的两个问题：基类有没有收到本轮的选项原值？Dressage 有没有开始读取 bwrap 配置？只为复现旧签名报错，第 1 次就够了。第 4 次还能抓住另一种错误：调用成功了，`"keep"` 却在转交时丢了。

### 5.3 当前结果与下次升级的通过条件

Harbor 0.26.0 上，修前只有旧测试通过，四个工厂用例全部失败。改写后的 C01 在原有五例行为回归之外增加了一个签名快照，**六例全部通过**。这组回归验证到后端开始预检，完整 Trial 启动另行验收。

**下次升级先检查上游入口。** 重跑正式测试 `test_harbor_preflight_signature` 时，它读取当前环境中安装的 Harbor。基线是 Harbor 0.26.0 的 `BaseEnvironment.preflight(kwargs=None)`。按顺序核对参数名、传参方式和默认值，无需启动 Trial。

```python
import inspect
from harbor.environments.base import BaseEnvironment


def test_harbor_preflight_signature():
    # Flag changes to the Harbor hook separately from the factory behavior tests.
    parameters = inspect.signature(BaseEnvironment.preflight).parameters.values()
    assert [(param.name, param.kind, param.default) for param in parameters] == [
        ("kwargs", inspect.Parameter.POSITIONAL_OR_KEYWORD, None),
    ]
```

**再验证行为。** 快照不匹配时，先查新版工厂实际传了什么。无论快照是否变化，都在候选版上复跑原有五例。若接口声明和实际行为均已核实兼容，再更新快照基线。快照已纳入 Dressage 的 pytest 套件。在 Harbor 0.18.0 上，新用例如期报出缺少 `kwargs`。

## 证据索引

复核这次提交，看 **⑤ 正式测试结果**。准备测试下一个 Harbor 版本，看 **下次升级复跑**。标有“调查 01”和“本地 PR-001”的入口都在本笔记仓库。

| 核对哪一节 | 打开后看什么 | 证据入口 |
| --- | --- | --- |
| ① 环境怎样接入 | 先看 Dressage 写进 Job 配置的类路径，再看 Harbor CLI 把这个路径和选项交给环境工厂。 | [Dressage DAPO 示例 · _job_payload](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/examples/harbor/dataset_tools/dapo/prepare_dataset.py#L350-L365) · [Harbor 0.26 CLI · _run_preflight](https://github.com/harbor-framework/harbor/blob/v0.26.0/src/harbor/cli/jobs.py#L113-L122) |
| ① 上游调用 | 对照 0.18 的无参调用和 0.26 的关键字调用。0.26 工厂从 CLI 接收配置选项，直接调用工厂并省略选项时取默认值 `None`。 | [Harbor 0.18 · factory.py](https://github.com/harbor-framework/harbor/blob/v0.18.0/src/harbor/environments/factory.py#L194-L205) · [Harbor 0.26 · factory.py](https://github.com/harbor-framework/harbor/blob/v0.26.0/src/harbor/environments/factory.py#L314-L324) |
| ② 修前现象 | 找 0.26 的报错行，看异常点名的是哪个关键字。 | [调查 01 · preflight-output.txt 第 4–8 行](../../../investigations/01-environment-preflight/preflight-output.txt#L4-L8) |
| ③ 失败位置 | 对照旧方法的形参和旧测试的实参，就能解释旧测试为什么通过。 | [Dressage 修前源码 · preflight 签名](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/environment.py#L301-L305) · [Dressage 修前测试 · 无参调用](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/tests/integrations/harbor/test_environment.py#L184-L188) |
| ④ 修复理由 | 先看基类要求转交什么，再查只改签名时为什么解析调用次数仍是 0。 | [Harbor 0.26 · BaseEnvironment.preflight](https://github.com/harbor-framework/harbor/blob/v0.26.0/src/harbor/environments/base.py#L1144-L1159) · [调查 01 · 三种实现的对照](../../../investigations/01-environment-preflight/README.md#runtime-comparison) |
| ⑤ 测试原文 | 在同一个文件中先定位旧的无参测试，再看新增工厂测试的四组输入和两条断言。本地也可以执行 `git show 8827b11 -- tests/integrations/harbor/test_environment.py` 查看本笔新增内容。 | [个人 Dressage 仓库 · C01 的三个预检测试函数](https://github.com/dextermayhewjd/Dressage/blob/8827b113a182bdf0f771747e82f5eafa4d04d10c/tests/integrations/harbor/test_environment.py#L162-L232) |
| ⑤ 正式测试结果 | 初版行为回归对照为修前 4 败 1 过、修后 5 过。新版 C01 另验签名快照，0.26 上六例通过。 | [调查 01 · 改写后六例复验](../../../investigations/01-environment-preflight/README.md#amended-check) |
| ⑤ 测试为何这样写 | 看漏调基类时解析次数怎样变化，以及清空字典后哪一例失败。 | [调查 01 · 只改签名的实测](../../../investigations/01-environment-preflight/README.md#runtime-comparison) · [调查 01 · 用非空选项检测内容丢失](../../../investigations/01-environment-preflight/README.md#nonempty-options) |
| 下次升级复跑 | 对同一份 Dressage 先跑已验证版，再跑候选版。看命令、通过条件和失败后的排查顺序。 | [复跑手册 · C01 环境预检](../../../tools/reproduce.md#c01-preflight-regression) |
| 提交复验 | 初版从个人 GitHub 分支取回 `435e9f2` 后，按 `-k preflight` 复验得到 `5 passed, 3 deselected`。 | [调查 01 · 远端取回与复验](../../../investigations/01-environment-preflight/README.md#private-clone-check) |
| PR 验收范围 | C01 依赖 Harbor 0.26 的基类签名。随版本切换一起验收完整 CLI Trial 和训练入口。 | [本地 PR-001 · 哪些入口还要验](../README.md#acceptance) |
