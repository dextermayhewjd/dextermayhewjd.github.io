# Step 014 固定版本源码摘录

固定提交：18868a79b0b083a093798a94ed0f8cb4f71b9c14。仅作静态定位；长实现并不都是本轮首读范围。

## examples/coding_agent_rl/generate.py:286–296

[固定源码](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/generate.py#L286-L296)

```python
                with trace_span(base_sample, "agent_run", record_error=False) as span:
                    agent_exit_code = await harness.run(
                        sb,
                        workdir=md["workdir"],
                        session_id=session_id,
                        adapter_url=adapter_url,
                        time_budget_sec=CONFIG.agent_time_budget_sec,
                        prompt=swe.SWE_PROMPT,
                    )
                    span.set("exit_code", agent_exit_code)
                agent_metrics = await harness.collect_metrics(sb, workdir=md["workdir"])
```

## slime/observability/trace_utils.py:58–111

[固定源码](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/observability/trace_utils.py#L58-L111)

```python
@dataclass
class TraceHandle:
    trace_id: str
    carrier: dict[str, Any]
    sample_id: int | str | None = None
    group_id: int | str | None = None
    attempt: int = 0
    parent_span_id: str | None = None


@dataclass
class TraceSpanContext:
    target: Sample | TraceHandle | list[Sample | TraceHandle]
    handles: list[TraceHandle]
    span_records: list[tuple[TraceHandle, str]] = field(default_factory=list)
    start_ts: float = 0.0
    end_attrs: dict[str, Any] = field(default_factory=dict)
    end_events: list[dict[str, Any]] = field(default_factory=list)
    closed: bool = False

    def set(self, key: str, value: Any) -> TraceSpanContext:
        self.end_attrs[key] = value
        self._sync_end_events({key: value})
        return self

    def update(self, attrs: dict[str, Any] | None) -> TraceSpanContext:
        try:
            if attrs:
                plain_attrs = dict(attrs)
                trace_children = plain_attrs.pop(TRACE_CHILDREN_KEY, None)
                if plain_attrs:
                    self.end_attrs.update(plain_attrs)
                    self._sync_end_events(plain_attrs)
                if trace_children:
                    _append_trace_children(self.span_records, trace_children, parent_start_ts=self.start_ts)
        except Exception as exc:
            _log_trace_error("update", exc)
        return self

    def build_end_attrs(self) -> dict[str, Any] | None:
        return dict(self.end_attrs) or None

    def finalize(self, end_events: list[dict[str, Any]]) -> None:
        self.end_events = end_events
        self.closed = True
        if self.end_attrs:
            self._sync_end_events(self.end_attrs)

    def _sync_end_events(self, attrs: dict[str, Any]) -> None:
        if not self.end_events or not attrs:
            return
        for event in self.end_events:
            event.setdefault("attrs", {})
            event["attrs"].update(attrs)
```

## slime/observability/trace_utils.py:238–254

[固定源码](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/observability/trace_utils.py#L238-L254)

```python
def bind_trace(sample: Sample) -> TraceHandle:
    try:
        sample.trace = _ensure_trace_carrier(
            getattr(sample, "trace", None),
            sample_id=sample.index,
            group_id=sample.group_index,
        )
        return TraceHandle(
            trace_id=sample.trace["trace_id"],
            carrier=sample.trace,
            sample_id=sample.trace.get("sample_id"),
            group_id=sample.trace.get("group_id"),
            attempt=int(sample.trace.get("attempt", 0)),
        )
    except Exception as exc:
        _log_trace_error("bind", exc)
        return _noop_handle()
```

## slime/observability/trace_utils.py:344–425

[固定源码](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/observability/trace_utils.py#L344-L425)

```python
@contextmanager
def trace_span(
    target: Sample | TraceHandle | list[Sample | TraceHandle],
    name: str,
    *,
    attrs: dict[str, Any] | None = None,
    record_error: bool = True,
):
    try:
        handles = _coerce_handles(target)
    except Exception as exc:
        _log_trace_error(f"span:{name}", exc)
        handles = []

    if not handles:
        yield target
        return

    timestamp = time.time()
    stack_before = _TRACE_STACK.get()
    handle_stack_before = _TRACE_HANDLE_STACK.get()
    span_records: list[tuple[TraceHandle, str]] = []
    new_entries: list[tuple[str, str]] = []

    try:
        for handle in handles:
            span_id = _new_span_id()
            parent_span_id = handle.parent_span_id or _get_current_parent_span_id(handle.trace_id, stack=stack_before)
            _append_event(
                handle,
                kind="span_start",
                name=name,
                timestamp=timestamp,
                span_id=span_id,
                parent_span_id=parent_span_id,
                attrs=attrs,
            )
            span_records.append((handle, span_id))
            new_entries.append((handle.trace_id, span_id))
        token = _TRACE_STACK.set(stack_before + tuple(new_entries))
        handle_token = _TRACE_HANDLE_STACK.set(handle_stack_before + (tuple(handles),))
    except Exception as exc:
        _log_trace_error(f"span:{name}", exc)
        yield target
        return

    span_context = TraceSpanContext(
        target=handles[0] if len(handles) == 1 else handles,
        handles=handles,
        span_records=span_records,
        start_ts=timestamp,
    )

    try:
        yield span_context
    except BaseException as exc:
        try:
            end_attrs = span_context.build_end_attrs()
            if record_error:
                error_attrs = {"error_type": type(exc).__name__, "error_message": str(exc)}
                if end_attrs:
                    end_attrs.update(error_attrs)
                else:
                    end_attrs = error_attrs
            span_context.finalize(_record_span_end(span_records, name=name, attrs=end_attrs))
        except Exception as trace_exc:
            _log_trace_error(f"span_end:{name}", trace_exc)
        raise
    else:
        try:
            span_context.finalize(_record_span_end(span_records, name=name, attrs=span_context.build_end_attrs()))
        except Exception as exc:
            _log_trace_error(f"span_end:{name}", exc)
    finally:
        try:
            _TRACE_STACK.reset(token)
        except Exception as exc:
            _log_trace_error(f"span_reset:{name}", exc)
        try:
            _TRACE_HANDLE_STACK.reset(handle_token)
        except Exception as exc:
            _log_trace_error(f"span_handle_reset:{name}", exc)
```

## slime/observability/trace_utils.py:499–518

[固定源码](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/observability/trace_utils.py#L499-L518)

```python
def _record_span_end(
    span_records: list[tuple[TraceHandle, str]],
    *,
    name: str,
    attrs: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    timestamp = time.time()
    events = []
    for handle, span_id in span_records:
        events.append(
            _append_event(
                handle,
                kind="span_end",
                name=name,
                timestamp=timestamp,
                span_id=span_id,
                attrs=attrs,
            )
        )
    return events
```

## slime/observability/trace_utils.py:587–627

[固定源码](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/observability/trace_utils.py#L587-L627)

```python
def _append_event(
    handle: TraceHandle,
    *,
    kind: str,
    name: str,
    timestamp: float,
    attrs: dict[str, Any] | None = None,
    span_id: str | None = None,
    parent_span_id: str | None = None,
) -> dict[str, Any]:
    event = {
        "type": kind,
        "name": name,
        "ts": timestamp,
        "trace_id": handle.trace_id,
        "sample_id": handle.sample_id,
        "group_id": handle.group_id,
        "attempt": int(handle.carrier.get("attempt", handle.attempt)),
    }
    if span_id is not None:
        event["span_id"] = span_id
    if parent_span_id is not None:
        event["parent_span_id"] = parent_span_id
    if attrs:
        event["attrs"] = dict(attrs)
    handle.carrier["events"].append(event)
    return event


def _coerce_handles(target: Sample | TraceHandle | list[Sample | TraceHandle]) -> list[TraceHandle]:
    target = _adapt_trace_target(target)
    if isinstance(target, TraceHandle):
        return [target]
    if isinstance(target, Sample):
        return [bind_trace(target)]
    if isinstance(target, list):
        handles = []
        for item in target:
            handles.extend(_coerce_handles(item))
        return handles
    return []
```
