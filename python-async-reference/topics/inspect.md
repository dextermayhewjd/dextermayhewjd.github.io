# inspect — Inspect live objects — Python 3.16.0a1 documentation

- 官方页面：https://docs.python.org/3.16/library/inspect.html
- 抓取状态：ok
- 纳入理由：Coroutine/awaitable/asynchronous-generator detection, state and locals inspection; full module reference retained.
- 范围：matched_sections

[总目录](../OFFICIAL-DOCS.md) · [跨主题统计](../TOPIC-USAGE.md)

## 1. 条目与调用位置数

**每格为：直接调用 / 推断方法 / 非调用引用。**

| API / 协议条目 | slime | areal | verl |
| --- | --- | --- | --- |
| [`inspect.CO_ASYNC_GENERATOR`](https://docs.python.org/3.16/library/inspect.html#inspect.CO_ASYNC_GENERATOR) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`inspect.CO_COROUTINE`](https://docs.python.org/3.16/library/inspect.html#inspect.CO_COROUTINE) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 1 |
| [`inspect.CO_ITERABLE_COROUTINE`](https://docs.python.org/3.16/library/inspect.html#inspect.CO_ITERABLE_COROUTINE) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`inspect.getasyncgenlocals`](https://docs.python.org/3.16/library/inspect.html#inspect.getasyncgenlocals) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`inspect.getasyncgenstate`](https://docs.python.org/3.16/library/inspect.html#inspect.getasyncgenstate) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`inspect.getcoroutinelocals`](https://docs.python.org/3.16/library/inspect.html#inspect.getcoroutinelocals) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`inspect.getcoroutinestate`](https://docs.python.org/3.16/library/inspect.html#inspect.getcoroutinestate) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`inspect.isasyncgen`](https://docs.python.org/3.16/library/inspect.html#inspect.isasyncgen) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`inspect.isasyncgenfunction`](https://docs.python.org/3.16/library/inspect.html#inspect.isasyncgenfunction) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`inspect.isawaitable`](https://docs.python.org/3.16/library/inspect.html#inspect.isawaitable) | 1 / 0 / 0 | 5 / 0 / 0 | 0 / 0 / 0 |
| [`inspect.iscoroutine`](https://docs.python.org/3.16/library/inspect.html#inspect.iscoroutine) | 0 / 0 / 0 | 0 / 0 / 0 | 1 / 0 / 0 |
| [`inspect.iscoroutinefunction`](https://docs.python.org/3.16/library/inspect.html#inspect.iscoroutinefunction) | 1 / 0 / 0 | 0 / 0 / 0 | 12 / 0 / 0 |
| [`inspect.markcoroutinefunction`](https://docs.python.org/3.16/library/inspect.html#inspect.markcoroutinefunction) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |

## 2. 本地源码位置

| 仓库 / 范围 | API | 记录种类 | 源码位置 | 原代码 |
| --- | --- | --- | --- | --- |
| slime / core | `inspect.iscoroutinefunction` | api_call | [slime/observability/trace_utils.py:460](../repositories/slime/source_snapshot/slime/observability/trace_utils.py.txt) · [固定版本](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/observability/trace_utils.py#L460) |         if inspect.iscoroutinefunction(fn): |
| slime / core | `inspect.isawaitable` | api_call | [slime/rollout/sample_hooks.py:41](../repositories/slime/source_snapshot/slime/rollout/sample_hooks.py.txt) · [固定版本](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/rollout/sample_hooks.py#L41) |         if inspect.isawaitable(result): |
| areal / core | `inspect.isawaitable` | api_call | [areal/experimental/openai/proxy/workflow.py:246](../repositories/areal/source_snapshot/areal/experimental/openai/proxy/workflow.py.txt) · [固定版本](https://github.com/areal-project/AReaL/blob/298412a40f5b84ae6b2042987e81777e6dd0f284/areal/experimental/openai/proxy/workflow.py#L246) |             if inspect.isawaitable(metadata): |
| areal / core | `inspect.isawaitable` | api_call | [areal/experimental/openai/proxy/workflow.py:281](../repositories/areal/source_snapshot/areal/experimental/openai/proxy/workflow.py.txt) · [固定版本](https://github.com/areal-project/AReaL/blob/298412a40f5b84ae6b2042987e81777e6dd0f284/areal/experimental/openai/proxy/workflow.py#L281) |         if inspect.isawaitable(result): |
| areal / core | `inspect.isawaitable` | api_call | [areal/experimental/openai/proxy/workflow.py:338](../repositories/areal/source_snapshot/areal/experimental/openai/proxy/workflow.py.txt) · [固定版本](https://github.com/areal-project/AReaL/blob/298412a40f5b84ae6b2042987e81777e6dd0f284/areal/experimental/openai/proxy/workflow.py#L338) |         if inspect.isawaitable(metadata): |
| areal / core | `inspect.isawaitable` | api_call | [areal/infra/utils/concurrent.py:93](../repositories/areal/source_snapshot/areal/infra/utils/concurrent.py.txt) · [固定版本](https://github.com/areal-project/AReaL/blob/298412a40f5b84ae6b2042987e81777e6dd0f284/areal/infra/utils/concurrent.py#L93) |     if inspect.isawaitable(result): |
| areal / core | `inspect.isawaitable` | api_call | [areal/infra/utils/concurrent.py:235](../repositories/areal/source_snapshot/areal/infra/utils/concurrent.py.txt) · [固定版本](https://github.com/areal-project/AReaL/blob/298412a40f5b84ae6b2042987e81777e6dd0f284/areal/infra/utils/concurrent.py#L235) |             if inspect.isawaitable(result): |
| verl / core | `inspect.iscoroutinefunction` | api_call | [verl/experimental/reward_loop/reward_manager/dapo.py:30](../repositories/verl/source_snapshot/verl/experimental/reward_loop/reward_manager/dapo.py.txt) · [固定版本](https://github.com/verl-project/verl/blob/1d367a4f459a43768f76312c0d3430a99ec46b8c/verl/experimental/reward_loop/reward_manager/dapo.py#L30) |         self.is_async_reward_score = inspect.iscoroutinefunction(self.compute_score) |
| verl / core | `inspect.iscoroutinefunction` | api_call | [verl/experimental/reward_loop/reward_manager/gdpo.py:30](../repositories/verl/source_snapshot/verl/experimental/reward_loop/reward_manager/gdpo.py.txt) · [固定版本](https://github.com/verl-project/verl/blob/1d367a4f459a43768f76312c0d3430a99ec46b8c/verl/experimental/reward_loop/reward_manager/gdpo.py#L30) |         self.is_async_reward_score = inspect.iscoroutinefunction(self.compute_score) |
| verl / core | `inspect.iscoroutinefunction` | api_call | [verl/experimental/reward_loop/reward_manager/limited.py:362](../repositories/verl/source_snapshot/verl/experimental/reward_loop/reward_manager/limited.py.txt) · [固定版本](https://github.com/verl-project/verl/blob/1d367a4f459a43768f76312c0d3430a99ec46b8c/verl/experimental/reward_loop/reward_manager/limited.py#L362) |         self.is_async_reward_score = inspect.iscoroutinefunction(self.compute_score) |
| verl / core | `inspect.iscoroutinefunction` | api_call | [verl/experimental/reward_loop/reward_manager/naive.py:30](../repositories/verl/source_snapshot/verl/experimental/reward_loop/reward_manager/naive.py.txt) · [固定版本](https://github.com/verl-project/verl/blob/1d367a4f459a43768f76312c0d3430a99ec46b8c/verl/experimental/reward_loop/reward_manager/naive.py#L30) |         self.is_async_reward_score = inspect.iscoroutinefunction(self.compute_score) |
| verl / core | `inspect.iscoroutinefunction` | api_call | [verl/experimental/reward_loop/reward_manager/remote.py:53](../repositories/verl/source_snapshot/verl/experimental/reward_loop/reward_manager/remote.py.txt) · [固定版本](https://github.com/verl-project/verl/blob/1d367a4f459a43768f76312c0d3430a99ec46b8c/verl/experimental/reward_loop/reward_manager/remote.py#L53) |         self.is_async_reward_score = inspect.iscoroutinefunction(self.compute_score) |
| verl / core | `inspect.iscoroutinefunction` | api_call | [verl/single_controller/base/decorator.py:439](../repositories/verl/source_snapshot/verl/single_controller/base/decorator.py.txt) · [固定版本](https://github.com/verl-project/verl/blob/1d367a4f459a43768f76312c0d3430a99ec46b8c/verl/single_controller/base/decorator.py#L439) |         wrapper = async_inner if inspect.iscoroutinefunction(func) else inner |
| verl / core | `inspect.iscoroutinefunction` | api_call | [verl/single_controller/ray/base.py:965](../repositories/verl/source_snapshot/verl/single_controller/ray/base.py.txt) · [固定版本](https://github.com/verl-project/verl/blob/1d367a4f459a43768f76312c0d3430a99ec46b8c/verl/single_controller/ray/base.py#L965) |                 wrapper = async_func if inspect.iscoroutinefunction(method) else func  # noqa: B023 |
| verl / core | `inspect.iscoroutinefunction` | api_call | [verl/tools/function_tool.py:118](../repositories/verl/source_snapshot/verl/tools/function_tool.py.txt) · [固定版本](https://github.com/verl-project/verl/blob/1d367a4f459a43768f76312c0d3430a99ec46b8c/verl/tools/function_tool.py#L118) |                 is_async=inspect.iscoroutinefunction(fn), |
| verl / core | `inspect.iscoroutinefunction` | api_call | [verl/trainer/ppo/reward.py:83](../repositories/verl/source_snapshot/verl/trainer/ppo/reward.py.txt) · [固定版本](https://github.com/verl-project/verl/blob/1d367a4f459a43768f76312c0d3430a99ec46b8c/verl/trainer/ppo/reward.py#L83) |     if not inspect.iscoroutinefunction(raw_fn): |
| verl / core | `inspect.iscoroutine` | api_call | [verl/utils/ray_utils.py:113](../repositories/verl/source_snapshot/verl/utils/ray_utils.py.txt) · [固定版本](https://github.com/verl-project/verl/blob/1d367a4f459a43768f76312c0d3430a99ec46b8c/verl/utils/ray_utils.py#L113) |         if not inspect.iscoroutine(coro): |
| verl / core | `inspect.CO_COROUTINE` | api_reference | [verl/utils/ray_utils.py:129](../repositories/verl/source_snapshot/verl/utils/ray_utils.py.txt) · [固定版本](https://github.com/verl-project/verl/blob/1d367a4f459a43768f76312c0d3430a99ec46b8c/verl/utils/ray_utils.py#L129) |         caller_is_async = caller_frame is not None and (caller_frame.f_code.co_flags &amp; inspect.CO_COROUTINE) != 0 |
| verl / core | `inspect.iscoroutinefunction` | api_call | [verl/utils/rollout_trace.py:471](../repositories/verl/source_snapshot/verl/utils/rollout_trace.py.txt) · [固定版本](https://github.com/verl-project/verl/blob/1d367a4f459a43768f76312c0d3430a99ec46b8c/verl/utils/rollout_trace.py#L471) |     return async_wrapper if inspect.iscoroutinefunction(func) else wrapper |
| verl / core | `inspect.iscoroutinefunction` | api_call | [verl/utils/skip/skip_manager.py:81](../repositories/verl/source_snapshot/verl/utils/skip/skip_manager.py.txt) · [固定版本](https://github.com/verl-project/verl/blob/1d367a4f459a43768f76312c0d3430a99ec46b8c/verl/utils/skip/skip_manager.py#L81) |             if inspect.iscoroutinefunction(func): |
| verl / core | `inspect.iscoroutinefunction` | api_call | [verl/utils/transferqueue_utils.py:476](../repositories/verl/source_snapshot/verl/utils/transferqueue_utils.py.txt) · [固定版本](https://github.com/verl-project/verl/blob/1d367a4f459a43768f76312c0d3430a99ec46b8c/verl/utils/transferqueue_utils.py#L476) |         wrapper = wrapper_async_inner if inspect.iscoroutinefunction(func) else wrapper_inner |
