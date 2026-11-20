# 00 · 这次向 Dressage 上游提交哪个 Harbor 版本？

**当前判断**　本次 Dressage 升级的唯一交付版本已确定为 `harbor==0.26.0`。0.18.0 是升级前基线，0.25.0 只用于定位行为从哪一版开始变化。

**对应的三版用法表**　[U01 安装 Dressage 的 Harbor extra](../../usage/启动与配置/U01-安装%20Dressage%20的%20Harbor%20extra.md#u01) · [U02 require_harbor_runtime 读取并检查发行包版本](../../usage/启动与配置/U02-require_harbor_runtime%20读取并检查发行包版本.md#u02) · [U34 EnvironmentFactory 调用 DressageEnvironment.preflight](../../usage/环境构造与生命周期/U34-EnvironmentFactory%20调用%20DressageEnvironment.preflight.md#u34) · [原套件在本问题测到了哪里](../original-test-audit.md#i00)

安装依赖、运行时版本检查和 PR 的运行验收统一使用 0.26.0。

<a id="sources"></a>

## 两边的源码原文

**Dressage 3e3142f**　可选依赖固定了升级前的版本。[pyproject.toml 第 21–22 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/pyproject.toml#L21-L22)

```toml
harbor = [
    "harbor==0.18.0",
```

**Harbor 0.25.0**　中间对照版的发布声明。[pyproject.toml 第 2–3 行](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/pyproject.toml#L2-L3)

```toml
name = "harbor"
version = "0.25.0"
```

**Harbor 0.26.0**　本次适配目标的发布声明。[pyproject.toml 第 2–3 行](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/pyproject.toml#L2-L3)

```toml
name = "harbor"
version = "0.26.0"
```

**据此判断**　0.25.0 和 0.26.0 都复现了日志挂载问题。0.26.0 的环境工厂还改变了预检传参，因此两项生产修复都要在 0.26.0 上从真实调用方复验。

<a id="evidence"></a>

## 证据与验证范围

**基线输出**　相同 Dressage 提交，排除端到端用例。[pytest-replay.txt 第 1–2 行](pytest-replay.txt#L1-L2)

```text
Harbor 0.18.0
66 passed, 8 deselected in 4.06s
```

**0.25 输出**　相同选择条件下的套件汇总。[pytest-replay.txt 第 8 行](pytest-replay.txt#L8)

```text
3 failed, 63 passed, 8 deselected in 4.04s
```

**0.26 输出**　相同选择条件下的套件汇总。[pytest-replay.txt 第 14 行](pytest-replay.txt#L14)

```text
3 failed, 63 passed, 8 deselected in 4.04s
```

两版的三个失败项也相同。套件计数用于比较基线，能否交付目标版取决于具体接入点修复后的验收。

## 处理与验收

**下一步**　在 0.26.0 的真实环境工厂和 Trial 日志回收入口验证修复，再从干净环境安装 Dressage 的 Harbor extra，核对实际安装的发行包版本。[01 工厂预检](../01-environment-preflight/README.md#evidence) · [02 日志回收](../02-output-mounts/README.md#mount-matrix) · [04 安装与版本检查](../04-version-checks/README.md)

**通过条件**　干净安装解析出 `harbor==0.26.0`，在这个安装环境运行集成套件、CLI rollout 与训练接入的代表性用例，并在 PR 登记实装版本、结果及排除项。[pytest 选择规则](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/pyproject.toml#L43) · [0.18 基线日志](pytest-0.18.0.txt) · [0.26 修前日志](pytest-0.26.0.txt) · [工厂探测输出](../01-environment-preflight/preflight-output.txt)

<a id="history"></a>

## 判断记录

- 2026-11-11　先由 0.18 与 0.25 的源码差异定位接口，再用真实调用决定改动范围。 [两个发布标签的源码对比](https://github.com/harbor-framework/harbor/compare/v0.18.0...v0.25.0)
- 2026-11-18　从独立 Dressage 仓库的 `3e3142f` 建立工作树 `Dressage-harbor-0.26`，分支为 `compat/harbor-0.26`。此前个人集成使用的 `3820149e` 属于另一条提交历史。
- 2026-11-18　本次对两个发布版本使用同一份独立 Dressage 代码做了工厂和文件回收探测，据此建议以 0.26.0 为本次 PR 的目标。完整 Trial 与训练接入的验收仍待实施。
- 2026-11-18　用户确认本次必须升级到 Harbor 0.26，交付目标锁定为发布包 `harbor==0.26.0`。0.25.0 的已有实验用于解释差异，修后通过与否以 0.26.0 的运行结果判定。

### 复查入口

- 复现与对照　[三版测试摘要](pytest-replay.txt) · [工厂签名](../01-environment-preflight/README.md) · [日志挂载](../02-output-mounts/README.md)
- 完整调用与配置　[pyproject.toml:22](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/pyproject.toml#L22) · [0.25 发布标签](https://github.com/harbor-framework/harbor/releases/tag/v0.25.0) · [0.26 发布标签](https://github.com/harbor-framework/harbor/releases/tag/v0.26.0)

[PR-001 如何审查此问题](../../prs/001-harbor-026-compatibility/README.md#scope) · [返回问题索引](../../README.md#investigations)
