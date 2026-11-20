# C03 · 让测试按 Harbor 0.26 的方式构造独立 verifier

**本笔决策**　修正测试夹具，让它像真实 Trial 那样分别构造 Agent 环境和独立评分环境。

修前 `8023acd` · Harbor 0.26.0 · 已推送 `600b8cd`。完整环境测试文件 12 项通过，无跳过。[Dressage 提交](https://github.com/dextermayhewjd/Dressage/commit/600b8cd74d1714a67df59fc406c1dbd97cb20e8a)

## ① 上游约定 · 独立 verifier 的自动清单只有评分目录

Harbor 0.26 创建独立 verifier 时，把本次评分环境的日志目录清单放进 `auto_mounts`。清单只含 `/logs/verifier`。`auto_mounts` 表示框架为该环境列出的挂载项，`auto_mounting` 才是是否执行自动绑定的开关。

## ② 修前表现 · 两个测试在准备 verifier 时失败

一个测试要检查 Agent 和 verifier 的网络及文件系统隔离，另一个要验证同一 bwrap 工作区可以先写文件再读回。它们都用 `_environment()` 辅助函数准备 verifier。两者在创建环境时就遇到 `ValueError: separate verifier does not have Harbor's verifier mount shape`，还没运行各自的断言。

## ③ 原因定位 · 夹具把评分目录传给了另一个参数

| 谁在构造 verifier | 哪个参数收到 `/logs/verifier` | 基类交给 Dressage 的完整清单 |
| --- | --- | --- |
| 旧测试夹具 | `mounts`，省略 `auto_mounts` | Harbor 补入默认项，清单含 agent、verifier、artifacts |
| Harbor 0.26 的真实 Trial | `auto_mounts` | 本例清单只含 verifier |

Dressage 用完整清单识别独立评分环境。测试给的会话名表示 verifier，清单却包含 Agent 目录，两条信息对不上。

## ④ 修复决策 · 只为独立 verifier 指定单项清单

在 `tests/integrations/harbor/test_environment.py` 的 `_environment()` 中，Agent 沿用 Harbor 默认的三个目标；独立 verifier 显式提供只含评分目录的自动清单。初稿给两个角色都传单项清单，普通用例虽通过，Agent 丢了 verifier 和 artifacts 两个目标。review 后在隔离测试中加入两条目标集合断言。

```python
auto_mounts = None  # Agent uses Harbor's default targets.
if verifier:
    auto_mounts = [
        {"type": "bind", "source": str(paths.verifier_dir), "target": "/logs/verifier"}
    ]
```

## ⑤ 回归验证 · 断言两个角色各自拿到的挂载目标

基线 C02 的环境测试为 10 过 2 败。初稿将两项失败修到通过，但新增的 Agent 清单断言在该初稿上失败，实测只有 `/logs/agent`。最终夹具在同一个 Harbor 0.26.0 环境中得到 `12 passed`，包含两个目标集合断言及原有的隔离和 bwrap 读写检查。verifier 启动时测试文件由谁准备，另见 C04。

## 证据索引

- 上游为独立 verifier 准备的清单及构造调用。[Harbor 0.26 的构造入口](https://github.com/harbor-framework/harbor/blob/v0.26.0/src/harbor/trial/trial.py#L1115-L1127)
- 省略自动清单后补默认项的条件，以及 Dressage 判断角色的位置。[Harbor 基类](https://github.com/harbor-framework/harbor/blob/v0.26.0/src/harbor/environments/base.py#L314-L340) · [Dressage 的角色判断](https://github.com/dextermayhewjd/Dressage/blob/8023acdaaba3fafe58a340a23e02608a6663a72a/dressage/integrations/harbor/environment.py#L238-L256)
- 两项原测试的修前夹具和早期基线实验。[C02 的测试夹具](https://github.com/dextermayhewjd/Dressage/blob/8023acdaaba3fafe58a340a23e02608a6663a72a/tests/integrations/harbor/test_environment.py#L52-L83) · [调查 03](../../../investigations/03-verifier-fixture/README.md)
