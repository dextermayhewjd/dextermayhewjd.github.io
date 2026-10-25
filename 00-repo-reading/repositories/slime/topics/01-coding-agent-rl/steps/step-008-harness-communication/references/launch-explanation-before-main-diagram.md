> 2026-10-24 恢复 launch_and_wait 整体主图前的网页段落，保留当时的 PID 与压缩说明。

---

<a id="launch-pid-compaction-18868a79"></a>

### 3.1 新版接续：启动 CLI、记录 PID 与处理压缩事件

以下依据 `18868a79`。前面的 `write_config` 写入 CLI 配置并注册 hook；`launch_and_wait` 为本次运行组装命令和环境变量，再交给下层执行。它不是在这里重新安装 Claude Code。

**PID 是操作系统给进程的编号。** 当前命令先启动 CLI，再用 `$!` 取得这个后台进程的 PID，写入本题目录的 `.harness/cli.pid`。它用来找到这一次运行的进程，不是软件版本或代码快照编号。

下面是启动命令中的相关片段，目录使用教学值；前一行的 CLI 命令已通过 `&` 在后台启动：

```bash
slime_cli_pid=$!
printf '%s\n' "$slime_cli_pid" > /workspace/repo/.harness/cli.pid
wait "$slime_cli_pid"
```

`wait` 等待这个 CLI 子进程结束。下层 `exec_and_wait` 另外安排启动脚本在命令结束后写入完成标记，Slime 通过该标记取得退出状态。

压缩由 Claude CLI 自身处理。Slime 在前后两个事件中运行已注册的 `run_hook`，记录次数并执行预算控制：

| 时刻 | 相关代码的作用 |
| --- | --- |
| 启动前 | 启动命令把 `compaction.json` 的计数与触限标志清零 |
| `PreCompact` | 检查是否允许这次压缩；放行时增加 `attempts` |
| `PostCompact` | 增加已完成次数 `count` |
| 下一次压缩前发现预算已用完 | 标记 `limit_reached`，读取 `cli.pid`，核验进程关系后向这次 CLI 发送 `SIGTERM` |

因此，这里分别留下两类信息：`compaction.json` 保存压缩计数，`cli.pid` 保存需要时应停止哪个进程。压缩后的上下文由 CLI 自己管理。

<details>
<summary>停止预算、源码与阅读边界</summary>

- `SLIME_AGENT_CC_MAX_COMPACTIONS` 默认 `-1`，表示不启用次数上限；设置非负值后才按预算阻止后续压缩尝试。
- 默认停止方式为信号模式，先核验记录的 PID 对应当前 hook 的祖先进程，再发送 `SIGTERM`。这里定位职责，具体的 `/proc` 读取和祖先遍历留待按需深入。
- [write_config：57–84](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/harness/claude_code.py#L57-L84)；[launch_and_wait：86–109](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/harness/claude_code.py#L86-L109)。
- [run_hook：23–68](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/harness/compaction.py#L23-L68)；[完成标记与等待：sandbox.py:124–162](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/sandbox.py#L124-L162)。
- 本次依据静态源码接清协作关系，没有执行真实 CLI、压缩或停止信号。

</details>
