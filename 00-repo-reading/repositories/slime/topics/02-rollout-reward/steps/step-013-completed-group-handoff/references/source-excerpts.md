# 本步的完整源码定位

固定提交：`18868a79b0b083a093798a94ed0f8cb4f71b9c14`。仅保存当前两个方法与调用交接，供核对教学裁剪；不代表已逐项阅读全部分支。

## 回调注册点

[原文件 211–223 行](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/fully_async_rollout.py#L211-L223)

```python
for group in groups:
    gid = gid_counter
    gid_counter += 1
    task = asyncio.create_task(
        generate_and_rm_group(
            self.args,
            group,
            sampling_params=self.state.sampling_params.copy(),
            evaluation=False,
        )
    )
    task.add_done_callback(self._make_done_cb(gid, group))
    active_tasks.add(task)
```

## AsyncRolloutWorker._make_done_cb

[原文件 246–275 行](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/fully_async_rollout.py#L246-L275)

```python
def _make_done_cb(self, gid: int, input_group: list[Sample]):
    # Interrupted segments cannot reopen their closed agent sessions.
    # Save their inputs before generation mutates them; completed siblings
    # will retain their results when the group is retried.
    retry_group = [sample if isinstance(sample, list) else copy.deepcopy(sample) for sample in input_group]

    def _cb(done_task: asyncio.Task) -> None:
        try:
            result = done_task.result()
        except asyncio.CancelledError:
            return
        except Exception as error:
            self.error = error
            return
        if not isinstance(result, list):
            logger.warning(
                "fully-async: generate_and_rm_group returned %r, expected list[Sample]; dropping",
                type(result).__name__,
            )
            return
        # The early weight-update exit may return untouched PENDING inputs.
        if any(s.status in (Sample.Status.ABORTED, Sample.Status.PENDING) for s in iter_samples(result)):
            try:
                self.data_buffer.add_samples([prepare_retry_group(retry_group, result)])
            except Exception:  # noqa: BLE001
                logger.exception("fully-async: failed to requeue aborted group")
            return
        self.output_queue.put((gid, result))

    return _cb
```

## AsyncRolloutWorker.get_completed_groups

[原文件 147–161 行](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/fully_async_rollout.py#L147-L161)

```python
def get_completed_groups(self, limit: int | None = None) -> list[tuple[int, list[Sample]]]:
    """Pop up to ``limit`` completed groups (all of them when ``None``).

    Callers that only need a fixed number of groups must pass ``limit`` —
    anything popped beyond it would otherwise have to be thrown away, and
    these groups are fully generated and reward-scored, with their prompts
    already consumed from ``data_buffer``.
    """
    completed: list[tuple[int, list[Sample]]] = []
    while limit is None or len(completed) < limit:
        try:
            completed.append(self.output_queue.get_nowait())
        except queue.Empty:
            break
    return completed
```

## 消费方的取组与筛选

[原文件 306–322 行](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/fully_async_rollout.py#L306-L322)

```python
while len(collected) < target:
    if worker.error is not None:
        raise worker.error
    # Pull only what this rollout still needs; the surplus stays queued for
    # the next rollout (that is the "queue stays warm" contract).
    drained = 0
    for _gid, group in worker.get_completed_groups(limit=target - len(collected)):
        drained += 1
        verdict = call_dynamic_filter(dynamic_filter, args, group)
        metric_gatherer.on_group_completed(verdict)
        if verdict.keep:
            if args.rollout_data_transport == "straw":
                group = await publish_rollout_async(
                    group, args, rollout_id, group=True, controller=getattr(data_buffer, "controller", None)
                )
            collected.append(group)
            continue
```
