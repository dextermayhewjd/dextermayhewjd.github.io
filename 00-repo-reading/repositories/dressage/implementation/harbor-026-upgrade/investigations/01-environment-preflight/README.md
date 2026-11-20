# 01 · 为什么 0.26 的环境工厂调不进 Dressage 的 bwrap 预检？

**当前判断**　C01 已改写并推送为 `8827b11`。使用 Harbor 0.26.0 运行五例行为回归和一例上游签名快照，六例全部通过。[改写后的验证](#amended-check)

**对应的三版用法表**　[U34 EnvironmentFactory 调用 DressageEnvironment.preflight](../../usage/环境构造与生命周期/U34-EnvironmentFactory%20调用%20DressageEnvironment.preflight.md#u34) · [原套件在本问题测到了哪里](../original-test-audit.md#i01)

<a id="implementation"></a>

## 动手前看什么，这笔修复怎样追踪？

Trial 排队前，Harbor 工厂实际调用 `env_class.preflight(kwargs=kwargs)`。修前的 Dressage 基线只接受 `cls`，所以直接调用后端的旧测试能通过，经工厂传选项却会报错。[两边的源码](#sources) · [正式工作树对照](#worktree-check)

| 这笔改动 | 当前记录 |
| --- | --- |
| 文件与行为 | 在 [Dressage 原有环境测试](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/tests/integrations/harbor/test_environment.py#L158-L184) 旁加入真实工厂回归；在 [DressageEnvironment.preflight](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/environment.py#L301-L305) 接收并转交选项，再执行原有后端检查。 |
| 正式验收 | 在修复提交上重跑默认输入、显式 `None`、空字典、含标记键的字典。每例均观察到基类收到原值、后端检查被调用，且原有预检用例通过。[回归输入和断言](test_factory_preflight.py#L16-L47) |
| Dressage 修复 SHA 与结果 | `8827b113a182bdf0f771747e82f5eafa4d04d10c`（父提交 `3e3142f`），六例预检通过。[实际命令和结果](#amended-check) |
| 关联提交与 PR | [C01 的改动范围与回归](../../prs/001-harbor-026-compatibility/commits/01-environment-preflight.md) · [PR-001 的提交计划](../../prs/001-harbor-026-compatibility/README.md#review-order)。上游 PR 待创建。 |

<a id="sources"></a>

## 两边的源码原文

**Dressage 3e3142f**　覆盖方法只声明了类参数。[environment.py 第 301–302 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/environment.py#L301-L302)

```python
@classmethod
def preflight(cls) -> None:
```

**Harbor 0.25.0**　自定义环境入口调用无参预检。[factory.py 第 272–274 行](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/environments/factory.py#L272-L274)

```python
env_class = import_symbol(import_path)
env_class.preflight()
return
```

**Harbor 0.26.0**　同一入口始终传入 `kwargs` 关键字。[factory.py 第 321–324 行](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/environments/factory.py#L321-L324)

```python
if import_path is not None:
    env_class = cls.get_environment_class(import_path=import_path)
    env_class.preflight(kwargs=kwargs)
    return
```

**据此判断**　0.26 在调用处多传一个关键字。当前 Dressage 方法在绑定参数时便失败，函数体里的 `bwrap` 检查还没开始。

<a id="evidence"></a>

## 证据与验证范围

**已存输出**　给两个工厂同一 import path，在 Dressage 的 `bwrap` 配置检查处设标记。[preflight-output.txt 第 4–8 行](preflight-output.txt#L4-L8)

```text
Harbor 0.25.0
factory entered Dressage's bwrap checks

Harbor 0.26.0
factory rejected the call: DressageEnvironment.preflight() got an unexpected keyword argument 'kwargs'
```

0.25 走到标记，0.26 在工厂调用处报错。这次探测覆盖方法签名，完整环境启动属于修后验收。

已有的 Dressage 测试直接调用 `DressageEnvironment.preflight()`。这条调用可以进入后端，覆盖不到 Harbor 工厂给它传关键字的一行。新增回归从真实的 `EnvironmentFactory.run_preflight` 进入，在首次读取 bwrap 配置处停止。0.26 还会检查基类是否收到原始选项。[原套件的直接调用](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/tests/integrations/harbor/test_environment.py#L158-L184) · [可执行回归](test_factory_preflight.py) · [修前三版 pytest 输出](factory-contract-results.txt)

| 原调用方给的输入 | 0.18.0 | 0.25.0 | 0.26.0 基线 |
| --- | --- | --- | --- |
| 仅给环境类路径，使用工厂默认值 | 到达后端检查 | 到达后端检查 | 工厂传入 `kwargs=None`，抛出 `TypeError` |
| 显式给 `kwargs=None` 或 `kwargs={}` | 工厂未提供该参数，两例跳过 | 工厂未提供该参数，两例跳过 | 两例都在调用后端时抛出相同的 `TypeError` |

## 处理与验收

**已实现**　覆盖方法接收可选 `kwargs`，先调用 `super().preflight(kwargs)` 交给基类解析选项，再执行已有的后端检查。[BaseEnvironment.preflight](https://github.com/harbor-framework/harbor/blob/v0.26.0/src/harbor/environments/base.py#L1144-L1159)

**通过条件**　经真实工厂传入的选项原样到达基类，随后进入 bwrap 检查。正式分支还要通过原有的后端预检用例。[test_environment.py:158](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/tests/integrations/harbor/test_environment.py#L158)

<a id="runtime-comparison"></a>

## 从运行结果判断该改哪一行

这次要验证的是“Harbor 能把选项交给 Dressage，并继续做后端预检”。从实际调用者进入，让 Harbor 自己决定传什么参数。只给类路径就足以复现。

```python
EnvironmentFactory.run_preflight(
    type=None,
    import_path="dressage.integrations.harbor.environment:DressageEnvironment",
)
```

在同一份 Dressage `3e3142f` 的临时副本上，固定 Harbor 0.26.0、测试和三种输入，只改后端方法。测试在两个位置观察基类收到的选项和后端读取 bwrap 配置的调用。[工厂调用及两条断言](test_factory_preflight.py#L31-L47)

| 临时副本中的改动 | 相同测试的结果 | 可以作出的判断 |
| --- | --- | --- |
| 原样运行 | 3 例全部报 `unexpected keyword argument 'kwargs'` | 工厂调用在参数绑定处失败，后端没有开始读取配置。 |
| 只给 `preflight` 加上可选 `kwargs` 参数 | 3 例都进入后端，但 `parse_options` 的实际调用次数是 0 | 第一个异常消失了，Harbor 要求的选项校验仍被跳过。 |
| 在方法开头再加 `super().preflight(kwargs)` | 工厂回归 3 例通过，原有 Dressage 预检用例也通过 | 默认值、显式 `None` 和空字典都经过基类解析，随后仍然执行后端检查。 |

最后撤去测试替身，提供本地 bwrap 配置，用上面同一个工厂入口实际执行预检并正常返回。这个结果验证到本机的后端预检，完整 Trial、模型调用和评分属于后续验收。实验改动只在临时副本，升级工作树仍保留原实现。[复跑测试的命令](../../tools/reproduce.md#run-probes)

<a id="nonempty-options"></a>

### 原来的三例能发现选项内容被清空吗？

在 `3e3142f` 的临时副本上加载 Harbor 0.26.0，故意将转交语句写为 `super().preflight(None if kwargs is None else {})`。它能保留 `None` 和空字典，但会丢掉任何非空字典的键值。用真实工厂运行 pytest 得到以下结果。

| 临时实现 | 输入 | 实测结果 |
| --- | --- | --- |
| 原始 Dressage 方法 | 当前四例 | 4 failed |
| 故意清空字典 | 原有三例 | 3 passed |
| 故意清空字典 | 原有三例，加 `{"test_marker": "keep"}` | 1 failed, 3 passed |
| 原样转交 `kwargs` | 相同四例 | 4 passed |

`test_marker` 仅作为追踪输入的标记。断言检查传入 `parse_options` 的内容，随后在读取 bwrap 配置处截停。这个实验验证参数交接，实际运行沙箱的证据另见上面的本地预检记录。

<a id="test-file-rehearsal"></a>

### 把新回归和原测试放在一起会看到什么？

取 Dressage `3e3142f` 的临时副本，加载 Harbor 0.26.0，在原 `tests/integrations/harbor/test_environment.py` 中追加[工厂回归样例](test_factory_preflight.py)。用 `python -m pytest --noconftest -p no:cacheprovider -q tests/integrations/harbor/test_environment.py -k preflight` 定向对照，隔离仓库级收尾钩子。

| 后端实现 | 选中的预检测试 | 实测结果 |
| --- | --- | --- |
| 修前 | 原有 bwrap 命令测试 | 1 passed |
| 修前 | 原用例与四个工厂输入 | 4 failed, 1 passed |
| 按 C01 接收并原样转交选项 | 同样五例 | 5 passed |

原用例在修前就能通过。四个新增输入覆盖工厂发出调用的时刻，能看到原用例触达不到的参数绑定错误。这个结果来自隔离副本，正式工作树的提交与复验另行登记。

### 如果在 0.18 写测试，怎样提前发现这次升级会失败？

在临时副本里复用旧测试 `test_preflight_uses_container_compatible_proc` 的配置、命令收集器和原有断言。把直接调用 `DressageEnvironment.preflight()` 的那一行换成真实工厂入口，测试只提供两版都有的环境类路径。

```python
EnvironmentFactory.run_preflight(
    type=None,
    import_path="dressage.integrations.harbor.environment:DressageEnvironment",
)
assert len(commands) == 1  # 后端走到了执行 bwrap 命令的位置，命令由旧测试的替身收集
```

这一个用例在 Harbor 0.18.0 + Dressage `3e3142f` 上通过。换成 Harbor 0.26.0 后，旧 Dressage 在工厂调用处报 `unexpected keyword argument 'kwargs'`。继续使用 0.26.0，切到修后 `435e9f2` 时通过。它能发现工厂调不动后端。正式 C01 回归还传入非空选项，检查基类有没有收到完整内容。

<a id="worktree-check"></a>

### C01 在独立工作树上的实际验证

在 `Dressage-harbor-0.26` 的 `compat/harbor-0.26` 分支，确认导入的是当前工作树的 Dressage 和由目标版本构建的本地 Harbor 包，`importlib.metadata.version("harbor") == "0.26.0"`。先在 `tests/integrations/harbor/test_environment.py` 加入四例工厂回归，保留原有直接调用测试。随后修改 `environment.py` 的方法签名和基类调用，两次运行相同命令。

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -B -m pytest \
  --confcutdir=tests/integrations/harbor -p no:cacheprovider -p pytest_asyncio.plugin \
  -o asyncio_default_fixture_loop_scope=function --tb=line -q \
  tests/integrations/harbor/test_environment.py -k preflight
```

修前为 `4 failed, 1 passed, 3 deselected`。四个新增用例均在 0.26 工厂第 323 行报 `unexpected keyword argument 'kwargs'`。修后为 `5 passed, 3 deselected`。`--confcutdir` 保留集成测试本身的配置，避开会清理工作树输出目录的仓库级钩子。本次只选预检测试，工厂回归在读取 bwrap 配置处截停，原测试检查生成的 bwrap 命令。提交前已核对暂存 diff 及其五例回归。提交后在 `435e9f2` 复验为 `5 passed, 3 deselected`，`git show --format= --check 435e9f2` 通过。

<a id="private-clone-check"></a>

### 推到自己的 GitHub 后，怎样确认别人取得的是经过验证的提交？

个人私有仓库 `dextermayhewjd/Dressage` 的 `main` 是基线 `3e3142f`。开发目录 `Dressage-harbor-0.26` 和验证目录 `Dressage-private` 都跟踪该仓库的 `origin/compat/harbor-0.26`。开发目录负责提交，验证目录拉取 GitHub 已收到的版本。验证目录最初从本机克隆，原来的 `source` 远端仍指向本机。

```bash
# 在开发目录完成一笔提交后
git -C /home/hongshi/projects/Dressage-harbor-0.26 push
git -C /home/hongshi/projects/Dressage-harbor-0.26 rev-parse HEAD

# 在验证目录拉取远端分支，核对两处输出的完整 SHA，再运行这笔提交对应的回归
git -C /home/hongshi/projects/Dressage-private pull --ff-only
git -C /home/hongshi/projects/Dressage-private rev-parse HEAD
```

**C01 的实际结果。** 先在本地独立克隆复验。随后推送升级分支，又从 GitHub 克隆到新的空目录，核对完整 SHA 为 `435e9f286f2aefbbaf58154468bc551f17aca2c7`，并确认 Python 导入的是这份克隆里的 `DressageEnvironment`。复用本机的 Python 环境和 Harbor 0.26.0 包，五例预检通过，三例未选中。结果来自本地 pytest；干净安装及完整 Trial 仍按 PR 的验收表执行。[个人仓库中的 C01](https://github.com/dextermayhewjd/Dressage/commit/435e9f286f2aefbbaf58154468bc551f17aca2c7) · [完整升级验收](../../prs/001-harbor-026-compatibility/README.md#acceptance)

<a id="amended-check"></a>

### 加入上游签名快照后重做 C01

原提交 `435e9f2` 改写为 `8827b11`，父提交仍为 `3e3142f`。新增 `test_harbor_preflight_signature` 仅检查参数名、顺序、传参方式和默认值。对候选提交运行本页预检命令（`-k preflight`），Harbor 0.26.0 得到 `6 passed, 3 deselected`。用 0.18.0 单独运行新增用例，实际为无参，预期含 `kwargs`，断言如期失败。个人远端分支 `compat/harbor-0.26` 已核对为同一提交。[新版 C01](https://github.com/dextermayhewjd/Dressage/commit/8827b113a182bdf0f771747e82f5eafa4d04d10c)

<a id="history"></a>

## 判断记录

- 在 `435e9f2` 导出的三个临时副本上，保留已提交的测试，用 Harbor 0.26.0 重跑同一组五例预检。原样运行五例通过。删去 `super().preflight(kwargs)` 后，四例工厂回归失败，原有直接调用用例通过。把非空字典清成 `{}` 后，只有 `nonempty-options` 失败，另外四例通过。这次对照说明已提交的回归能发现两种错误修法，观察终点是后端开始读 bwrap 配置。[对应的测试和断言](../../prs/001-harbor-026-compatibility/commits/01-environment-preflight.md)
- 2026-11-18　用两个版本的真实工厂将同一 import path 解析为独立 Dressage 工作树中的类。在 bwrap 配置检查处放入测试标记，0.25 到达标记，0.26 在参数绑定处报错。这个实验验证调用签名，完整的 bwrap 启动另行验收。
- 2026-11-18　把相同工厂调用变成 pytest 断言。0.26 的默认值、显式 `None` 和空字典三例都在工厂第 323 行失败。修后用同一文件检验选项交接与后端入口。[断言和输入](test_factory_preflight.py) · [实测输出](factory-contract-results.txt)
- 2026-11-19　在正式工作树 `compat/harbor-0.26` 的未修改提交 `3e3142f` 重放，确认 Dressage 从该工作树导入、Harbor 从本地 0.26.0 包导入。真实工厂的三种调用均报 `unexpected keyword argument 'kwargs'`。直接调用后端的原有测试单独通过。两次对照使用 `--noconftest` 隔离仓库级收尾钩子，范围为预检。接下来在这个提交上加入工厂回归，修改后端方法，用相同输入复验。[三种工厂输入](test_factory_preflight.py) · [原有预检用例](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/tests/integrations/harbor/test_environment.py#L158-L184)

- 2026-11-19　在 Dressage 升级工作树提交 `435e9f2`，其中包含后端实现和工厂入口回归。在该提交上用 Harbor 0.26.0 复验五例通过。上游 PR 待创建。[提交过程](../../prs/001-harbor-026-compatibility/commits/01-environment-preflight.md)

### 复查入口

- 复现与对照　[探测脚本](probe.py) · [三版输出](preflight-output.txt) · [复现环境](../../tools/reproduce.md#setup)
- 完整调用与配置　[environment.py:302](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/environment.py#L302) · [0.26 factory.py:314](https://github.com/harbor-framework/harbor/blob/v0.26.0/src/harbor/environments/factory.py#L314-L330) · [0.25 factory.py:265](https://github.com/harbor-framework/harbor/blob/v0.25.0/src/harbor/environments/factory.py#L265-L280)

[PR-001 如何审查此问题](../../prs/001-harbor-026-compatibility/README.md#preflight) · [返回问题索引](../../README.md#investigations)
