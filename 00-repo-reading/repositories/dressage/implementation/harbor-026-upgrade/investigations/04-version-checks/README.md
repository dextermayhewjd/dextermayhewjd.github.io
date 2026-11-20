# 04 · 哪些地方仍要求安装和运行 Harbor 0.18.0？

**当前判断**　本次安装和运行声明统一锁定为 `harbor==0.26.0`。Dressage 基线目前仍要求 0.18.0，直接运行会拒绝 0.26.0。

**对应的三版用法表**　[U01 安装 Dressage 的 Harbor extra](../../usage/启动与配置/U01-安装%20Dressage%20的%20Harbor%20extra.md#u01) · [U02 require_harbor_runtime 读取并检查发行包版本](../../usage/启动与配置/U02-require_harbor_runtime%20读取并检查发行包版本.md#u02) · [U03 DAPO 命令的 check_runtime 读取同一包版本](../../usage/启动与配置/U03-DAPO%20命令的%20check_runtime%20读取同一包版本.md#u03) · [U04 harbor run 发现并挂接 --plugin dressage](../../usage/启动与配置/U04-harbor%20run%20发现并挂接%20--plugin%20dressage.md#u04) · [原套件在本问题测到了哪里](../original-test-audit.md#i04)

即使后端行为适配成功，用户也需要能从声明的依赖安装并启动相同版本。

<a id="sources"></a>

## 两边的源码原文

**Dressage 3e3142f**　`require_harbor_runtime` 拒绝与指定版本不相等的值。[compat.py 第 57–60 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/compat.py#L57-L60)

```python
if harbor_version != SUPPORTED_HARBOR_VERSION:
    raise HarborCompatibilityError(
        f"unsupported Harbor version {harbor_version!r}; expected exactly {SUPPORTED_HARBOR_VERSION!r}"
    )
```

**Harbor 0.26.0**　运行时读到的目标包版本。[pyproject.toml 第 2–3 行](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/pyproject.toml#L2-L3)

```toml
name = "harbor"
version = "0.26.0"
```

**Harbor 0.26.0**　该包对 Python 的最低要求。[pyproject.toml 第 9 行](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/pyproject.toml#L9)

```toml
requires-python = ">=3.12"
```

**据此判断**　安装 extra 固定 0.18.0，运行时还检查精确版本。把 0.26 装进实验环境后仍会命中版本检查。安装声明、运行时、DAPO 工具和文档应随完成验收的版本同步更新。

<a id="evidence"></a>

## 证据与验证范围

**已存输出**　探测在任何临时放行之前先运行原版本检查。[trial-plan-output.txt 第 19–20 行](../09-trial-plan/trial-plan-output.txt#L19-L20)

```text
Harbor 0.26.0
original version check: unsupported Harbor version '0.26.0'; expected exactly '0.18.0'
```

随后只在探测进程内临时放行所测版本。另从固定 Dressage 提交构建 wheel，在临时目录离线安装该 wheel。两个 Harbor 版本都从短名 `dressage` 解析到正确的插件类。wheel 的 extra 仍声明 0.18.0。逐项匹配 0.26 基础依赖发现，本机共用实验环境缺少 `semver` 和 `fastmcp`。这说明目前的测试环境可以验证特定调用，却不能作为干净安装已经通过的证据。[实测元数据](wheel-output.txt) · [探测程序](wheel_probe.py) · [0.26 的依赖原文](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/pyproject.toml#L10-L37)

## 处理与验收

**下一步**　把 extra 的精确依赖、两处运行时版本检查、合同测试与安装示例同步到 0.26.0。维持普通 Dressage 包与可选 Harbor 集成的导入边界。[安装说明](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/docs/harbor.md#L51) · [可选模块入口](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/__init__.py#L1)

**通过条件**　在干净的 Python 3.12 环境安装 extra 后，`importlib.metadata.version("harbor")` 返回 `"0.26.0"`，运行时检查通过，DAPO 的 `--check-runtime` 退出码为 0。精确版本检查遇到 0.25.0 时应报告版本不匹配。[运行时合同测试](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/tests/integrations/harbor/test_contracts.py#L108) · [旧版断言位置](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/tests/integrations/harbor/test_contracts.py#L165)

<a id="history"></a>

## 判断记录

- 2026-11-18　0.26 默认套件的第三项失败来自 `test_official_jobs_validate_with_harbor_018` 的旧版本断言，发生在 YAML 校验之前。该结果能定位版本限制，YAML 兼容性另有直接验证。
- 2026-11-18　单独运行 DAPO 命令的 `--check-runtime`。0.18.0 退出 0 且无输出，0.25.0、0.26.0 都退出 2 并显示期望与实装版本。 [三版实际退出码与报错](dapo-runtime-output.txt)

### 复查入口

- 复现与对照　[测试失败项](../00-version-target/pytest-replay.txt) · [原版本检查输出](../09-trial-plan/trial-plan-output.txt) · [问题 18](../18-example-configs/README.md)
- 完整调用与配置　[pyproject.toml:21](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/pyproject.toml#L21-L27) · [compat.py:37](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/compat.py#L37-L60) · [prepare_dataset.py:556](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/examples/harbor/dataset_tools/dapo/prepare_dataset.py#L556) · [Harbor pyproject.toml:3、9](https://github.com/harbor-framework/harbor/blob/v0.26.0/pyproject.toml#L1-L12)

[PR-001 的 C06 · 版本声明](../../prs/001-harbor-026-compatibility/README.md#versions) · [返回问题索引](../../README.md#investigations)
