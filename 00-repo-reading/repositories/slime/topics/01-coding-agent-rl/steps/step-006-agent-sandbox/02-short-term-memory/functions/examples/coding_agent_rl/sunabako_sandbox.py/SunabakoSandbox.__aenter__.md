# SunabakoSandbox.__aenter__

- 源码定位：[examples/coding_agent_rl/sunabako_sandbox.py:35–82](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/sunabako_sandbox.py#L35-L82)。
- 首次接触：Step 006，2026-10-24，从 `boot_agent_sandbox:132` 进入。
- 最近认识更新：2026-10-24，用户概括进入时通过 image 启动环境；镜像标识、配置与 SDK 创建之间的关系由助手补清。

[前一段：__init__](SunabakoSandbox.__init__.md) · [配套退出：__aexit__](SunabakoSandbox.__aexit__.md) · [父函数](../generate.py/boot_agent_sandbox.md#2-进入环境并准备-cli132143)

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：`cand` 已有初始字段，现在需要准备本次任务的执行环境。
2. **具体内容**：读取节点与镜像配置，调用 Sunabako SDK 创建环境，保存 SDK 操作对象、运行方式和沙箱编号；按配置记录创建清单，最后返回自身。
3. **建议构建的心智模型**：

   > 按已保存的镜像标识找到创建资料，让 SDK 准备环境，再把操作这份环境的入口放回同一个对象。

4. **调用代码**（`boot_agent_sandbox:132、135`，省略追踪与失败包装）：

   ```python
   await cand.__aenter__()
   await (harness or HARNESS_CLS()).install_cli(cand)
   ```

## 本场景的输入与输出

接住 [`__init__`](SunabakoSandbox.__init__.md) 得到的 `cand`。沿用 `image="example-image"`，假设创建成功、未设置 `SUNABAKO_ARTIFACTS`，运行方式采用默认的 `proot`。这是教学场景，未读取真实部署配置。

- **输入**：`self.image`，以及主机环境变量指向的集群配置文件和镜像映射 JSON；资源与环境选项保留在下方折叠区。
- **输出**：返回原对象 `self`。父函数没有接这个返回值，继续使用已经更新的 `cand`。
- **状态变化**：`_sandbox` 得到 SDK 操作对象，`sandbox_id` 得到其编号，`_runtime` 记录运行方式，`_workdir` 按镜像配置更新。CLI 随后才由父函数安排安装。

<a id="sunabako-enter-config"></a>

### 1. 根据镜像标识找到创建资料（38–41）

```python
cluster = Cluster.from_file(os.environ["SUNABAKO_CLUSTER"])
images = json.loads(Path(os.environ["SUNABAKO_IMAGES"]).read_text())
info = images[self.image]  # 用初始化时保存的镜像标识查这一项
self._workdir = info.get("workdir", "/testbed")
```

`SUNABAKO_CLUSTER` 指向提供可分配节点信息的配置文件；`SUNABAKO_IMAGES` 指向镜像映射 JSON。两份文件在运行 Slime 的主机上读取，`info` 是本次镜像的配置。

只展示本例用到的镜像配置形状，路径为占位：

```python
images = {
    "example-image": {
        "rootfs": "/shared/images/example-rootfs",
        "workdir": "/testbed",
    }
}
```

`rootfs` 指向所选节点能够访问的镜像或根文件系统材料；`workdir` 是环境内的工作目录路径。本段取得资料并更新路径字段，实际创建发生在下一段。

<a id="sunabako-enter-create"></a>

### 2. 创建环境，把操作入口保存回 cand（59–72、82）

以下为成功路径的教学裁剪，省略创建调用中的资源、网络和环境变量参数，以及日志、可选清单与失败包装；完整创建参数紧随其后折叠保存。

```python
runtime = os.environ.get("SUNABAKO_RUNTIME", "proot")
self._sandbox = await AsyncSandbox.create(
    info["rootfs"],
    cluster=cluster,
    runtime=runtime,
)
self._runtime = runtime
self.sandbox_id = self._sandbox.sandbox_id
return self
```

这里的 `AsyncSandbox` 来自 `sunabako` SDK。`self._sandbox` 保存的是本地 SDK 操作对象，后续通过它控制节点上的执行环境；`self` / `cand` 仍是外面那层 Slime 封装对象。二者都不能直接等同于环境内运行的进程。

返回 `boot_agent_sandbox:135` 后，同一个 `cand` 才交给 `install_cli`。本方法使环境就绪，未执行那次 CLI 安装。配套的[退出方法](SunabakoSandbox.__aexit__.md)随后用 `_sandbox` 请求回收。

<details>
<summary>原始创建参数与环境覆盖（42–70）</summary>

`overrides` 只收集主机上已设置的代理变量（大小写两组 `http_proxy`、`https_proxy`、`no_proxy`）及 `OMP_NUM_THREADS`、`OPENBLAS_NUM_THREADS`、`MKL_NUM_THREADS`、`NUMEXPR_NUM_THREADS`、`GOMAXPROCS`。合并时它们覆盖镜像配置中的同名变量。

```python
runtime = os.environ.get("SUNABAKO_RUNTIME", "proot")
self._sandbox = await AsyncSandbox.create(
    info["rootfs"],
    cluster=cluster,
    runtime=runtime,
    network="host",
    memory_mb=int(info.get("memory_mb", os.environ.get("SUNABAKO_MEMORY_MB", "2048"))),
    create_timeout=float(os.environ.get("SUNABAKO_CREATE_TIMEOUT_SEC", "600")),
    pids_max=int(info.get("pids_max", os.environ.get("SUNABAKO_PIDS_MAX", "256"))),
    memory_mode="rss" if os.environ.get("SUNABAKO_ALLOW_TEST_MEMORY") == "1" else "cgroup",
    envs={**info.get("env", {}), **overrides},
)
```

这里传递的是后端创建选项；节点选择、运行方式、资源限制和网络的具体实现留在 SDK 边界之外，当前只核对实参。

</details>

<details>
<summary>可选创建清单与失败边界（73–81）</summary>

设置 `SUNABAKO_ARTIFACTS` 时，在本机的对应沙箱编号目录保存创建清单，记录镜像、编号和节点。清单写入发生在返回前，便于之后识别本次创建的环境；若 `_save_manifest` 抛出普通异常，会先请求 `kill` 再重新抛出。若 `kill` 自身失败，其异常也可能向外传播。

读取配置、查找镜像或 SDK 创建失败时，本方法没有正常返回。SDK 创建部分失败后的资源处理由下层决定，不能从这里推断已经全部回收。

</details>

## 我的直接表述（原话）

2026-10-24，三个方法连读后的表述节选：

> 2.然后这里在进入的时候是通过这样子的image快速把这里的image拉起来

完整原话与“按 image 查找配置，再交给 SDK 创建环境”的澄清见[本轮反馈](../../../../../04-flow.md#sunabako-lifecycle-restatement)。原话中的“快速”保留其表达，不作为启动性能的验证结论；此前[范围确认](../../../../../04-flow.md#sunabako-lifecycle-methods)保留。

## 尚不清楚

- SDK 怎样选节点、建立执行环境与通信；实际部署配置和真实沙箱编号。
- 部分创建失败、取消及资源限制的实际行为；本轮未进行真实后端验证。

<details>
<summary>源码与验证范围</summary>

- 固定版本 `18868a79b0b083a093798a94ed0f8cb4f71b9c14`；源码与调用位置已静态核对。
- 创建清单的辅助实现见同文件 [105–109](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/sunabako_sandbox.py#L105-L109)，只用于核对产物含义，未继续深入。
- 本例为教学构造；没有读取用户的集群配置、安装 SDK 或创建沙箱。
- [本次连读记录](../../../../../04-flow.md#sunabako-lifecycle-methods)。

</details>
