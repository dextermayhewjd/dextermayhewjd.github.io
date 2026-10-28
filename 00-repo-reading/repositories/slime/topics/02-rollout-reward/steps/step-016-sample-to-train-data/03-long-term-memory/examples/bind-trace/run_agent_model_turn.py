"""Execute the real Trace implementation and Adapter with statement.

The source checkout is read-only. Only business dependencies of the selected
with statement are substituted; timestamps, span IDs, binding, and event writes
come from Slime's original implementation. No model or HTTP server is started.
"""

from __future__ import annotations

import __future__
import argparse
import ast
import asyncio
import contextvars
import copy
import dataclasses
import enum
import hashlib
import json
import subprocess
import sys
from contextlib import nullcontext
from datetime import datetime, timezone
from pathlib import Path
from types import MethodType, ModuleType, SimpleNamespace


HERE = Path(__file__).resolve().parent
REVISION = "18868a79b0b083a093798a94ed0f8cb4f71b9c14"
SOURCE_HASHES = {
    "slime/utils/types.py": "0843363f908b219fa5f91f013da3dcb25704f3cd3609ef1da04b0de691d8b66e",
    "slime/observability/trace_utils.py": "f7414a68ccfbc64bb887eaacaf1f04297289d113993b83b301c745a2057a5df7",
    "slime/agent/adapters/common.py": "afe3b9f728e1b7c4e2860fd0ea8ba27ae3623b8d801788baff8d4a0941eae76c",
    "examples/coding_agent_rl/generate.py": "974fa90dd781fc77c27e8d6447c1487c919ed3b3d97de4cebef7793b7f2000e5",
}


def isolated_module(name, **values):
    module = ModuleType(name)
    sys.modules[name] = module
    module.__dict__.update(values)
    return module


def execute_nodes(nodes, namespace, source_path):
    tree = ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[]))
    exec(
        compile(tree, str(source_path), "exec", flags=__future__.annotations.compiler_flag),
        namespace,
    )


def run(source_repo):
    actual_revision = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=source_repo, text=True
    ).strip()
    if actual_revision != REVISION:
        raise ValueError(f"Expected source revision {REVISION}, got {actual_revision}")
    for relative, expected_hash in SOURCE_HASHES.items():
        actual_hash = hashlib.sha256((source_repo / relative).read_bytes()).hexdigest()
        if actual_hash != expected_hash:
            raise ValueError(f"Source changed: {relative}")

    fixture = json.loads((HERE / "input.json").read_text())
    started_at = datetime.now(timezone.utc).isoformat()
    sample_path = source_repo / "slime/utils/types.py"
    sample_class = next(
        node for node in ast.parse(sample_path.read_text()).body
        if isinstance(node, ast.ClassDef) and node.name == "Sample"
    )
    sample_module = isolated_module(
        "trace_demo_sample", dataclass=dataclasses.dataclass,
        field=dataclasses.field, Enum=enum.Enum,
    )
    execute_nodes([sample_class], sample_module.__dict__, sample_path)
    sample_data = copy.deepcopy(fixture["base_sample"])
    initial_trace = sample_data.pop("trace")
    sample = sample_module.Sample(**sample_data)
    sample.trace = initial_trace

    # Load all original Trace code; wire its Sample import to the original class
    # loaded above, avoiding unrelated numpy/torch dependencies in types.py.
    trace_path = source_repo / "slime/observability/trace_utils.py"
    trace_tree = ast.parse(trace_path.read_text())
    trace_nodes = [
        node for node in trace_tree.body
        if not (isinstance(node, ast.ImportFrom) and node.module == "slime.utils.types")
    ]
    trace = isolated_module("trace_demo_utils", Sample=sample_module.Sample)
    execute_nodes(trace_nodes, trace.__dict__, trace_path)

    adapter_path = source_repo / "slime/agent/adapters/common.py"
    adapter_tree = ast.parse(adapter_path.read_text())
    session_class = next(
        node for node in adapter_tree.body
        if isinstance(node, ast.ClassDef) and node.name == "Session"
    )
    adapter_class = next(
        node for node in adapter_tree.body
        if isinstance(node, ast.ClassDef) and node.name == "BaseAdapter"
    )
    open_session = next(
        node for node in adapter_class.body
        if isinstance(node, ast.FunctionDef) and node.name == "open_session"
    )
    turn_function = next(
        node for node in adapter_class.body
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "_run_turn"
    )
    session_module = isolated_module("trace_demo_session", dataclasses=dataclasses)
    execute_nodes([session_class, open_session], session_module.__dict__, adapter_path)
    adapter = SimpleNamespace(store={})
    adapter.open_session = MethodType(session_module.open_session, adapter)

    generate_path = source_repo / "examples/coding_agent_rl/generate.py"
    create_session_call = next(
        node for node in ast.walk(ast.parse(generate_path.read_text()))
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        and node.func.attr == "open_session"
    )
    before_binding = copy.deepcopy(sample.trace)
    parent = fixture["active_context"]
    parent_handle = trace.bind_trace(sample)
    token = trace._TRACE_STACK.set(((parent["trace_id"], parent["span_id"]),))
    handle_token = trace._TRACE_HANDLE_STACK.set(((parent_handle,),))
    try:
        execute_nodes(
            [ast.Expr(value=create_session_call)],
            dict(
                adapter=adapter, session_id=fixture["session_id"], base_sample=sample,
                bind_trace=trace.bind_trace, export_trace=trace.export_trace,
                import_trace=trace.import_trace,
                sampling_params=fixture["sampling_defaults"],
                state=SimpleNamespace(max_context_len=fixture["max_context_tokens"]),
                args=SimpleNamespace(apply_chat_template_kwargs={}),
            ),
            generate_path,
        )
    finally:
        trace._TRACE_STACK.reset(token)
        trace._TRACE_HANDLE_STACK.reset(handle_token)
    after_binding = copy.deepcopy(sample.trace)
    session = adapter.store[fixture["session_id"]]

    # Find the original with statement including its conditional nullcontext,
    # nested agent_tokenize span, and awaited model call. Its body is unchanged.
    span_node = next(
        node for node in ast.walk(turn_function)
        if isinstance(node, ast.With)
        and isinstance(node.items[0].context_expr, ast.IfExp)
        and isinstance(node.items[0].context_expr.body, ast.Call)
        and isinstance(node.items[0].context_expr.body.func, ast.Name)
        and node.items[0].context_expr.body.func.id == "trace_span"
        and node.items[0].context_expr.body.args[1].value == "agent_model_turn"
    )
    observations = []

    def observe(stage):
        observations.append({
            "stage": stage,
            "event_count": len(sample.trace["events"]),
            "active_stack": [list(item) for item in trace._TRACE_STACK.get()],
        })

    def translate_stub(body):
        observe("inside_agent_tokenize")
        return copy.deepcopy(body["messages"]), None

    def prompt_ids_stub(messages, tokenizer, *, tools, session):
        return [51]

    async def model_stub(prompt_ids, session, body, *, adapter, session_id):
        observe("inside_model_call_stub_after_tokenize")
        await asyncio.sleep(0)
        return SimpleNamespace(output_ids=[52], finish_reason="stop")

    adapter._translate = translate_stub
    namespace = dict(
        self=adapter, s=session, sid=fixture["session_id"],
        body={"messages": [{"role": "user", "content": sample.prompt}]},
        tok=object(), trace_span=trace.trace_span,
        bind_trace_carrier=trace.bind_trace_carrier, nullcontext=nullcontext,
        _session_prompt_ids=prompt_ids_stub, call_sglang_generate=model_stub,
    )
    wrapper = ast.parse("async def run_original_excerpt():\n    pass").body[0]
    wrapper.body = [copy.deepcopy(span_node)]
    execute_nodes([wrapper], namespace, adapter_path)

    async def execute_request():
        observe("before_request_empty_context")
        await namespace["run_original_excerpt"]()
        observe("after_request_context_restored")

    # The request runs with empty ContextVars. Its parent comes from the
    # explicitly passed Session.trace, not an inherited producer context.
    contextvars.Context().run(lambda: asyncio.run(execute_request()))
    after_request = copy.deepcopy(sample.trace)
    events = after_request["events"][len(after_binding["events"]):]
    expected_order = [
        ("span_start", "agent_model_turn"), ("span_start", "agent_tokenize"),
        ("span_end", "agent_tokenize"), ("span_end", "agent_model_turn"),
    ]
    assert before_binding == after_binding
    assert [(event["type"], event["name"]) for event in events] == expected_order
    assert events[0]["parent_span_id"] == parent["span_id"]
    assert events[1]["parent_span_id"] == events[0]["span_id"]
    assert events[2]["span_id"] == events[1]["span_id"]
    assert events[3]["span_id"] == events[0]["span_id"]
    assert all(event["trace_id"] == sample.trace["trace_id"] for event in events)
    assert observations[0]["active_stack"] == observations[-1]["active_stack"] == []
    assert [item["event_count"] for item in observations] == [1, 3, 4, 5]
    assert session.trace.carrier is sample.trace

    return {
        "execution": {
            "status": "passed", "started_at_utc": started_at,
            "source_revision": actual_revision, "source_file_sha256": SOURCE_HASHES,
            "executed_original_code": [
                "Sample and Session classes; complete trace_utils implementation",
                "BaseAdapter.open_session and generate.py's original call expression",
                f"BaseAdapter._run_turn original with statement, lines {span_node.lineno}-{span_node.end_lineno}",
            ],
            "substituted_business_functions": {
                "self._translate": "returns the input message list and tools=None",
                "_session_prompt_ids": "returns [51]; no tokenizer run",
                "call_sglang_generate": "async stub returns output_ids=[52], finish_reason=stop",
            },
            "timestamp_source": "original time.time; not fixed or substituted",
            "span_id_source": "original uuid.uuid4().hex; not fixed or substituted",
            "initial_state": "input.json's teaching fixture T3/C0 with one preexisting event",
            "not_executed": "full _run_turn before/after the excerpt, HTTP server, actual tokenizer, model, Agent CLI",
            "harness_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "input_sha256": hashlib.sha256((HERE / "input.json").read_bytes()).hexdigest(),
        },
        "before_binding": before_binding,
        "after_binding": after_binding,
        "session_trace": {
            "trace_id": session.trace.trace_id,
            "parent_span_id": session.trace.parent_span_id,
            "carrier_is_sample_trace": session.trace.carrier is sample.trace,
        },
        "observations": observations,
        "after_agent_model_turn": after_request,
        "new_events": events,
        "new_event_count": len(events),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-repo", type=Path, default=Path("/home/hongshi/projects/slime"))
    parser.add_argument("--output", type=Path, default=HERE / "agent-model-turn-actual.json")
    args = parser.parse_args()
    result = run(args.source_repo.resolve())
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({
        "status": result["execution"]["status"],
        "events_after_binding": len(result["after_binding"]["events"]),
        "events_after_excerpt": len(result["after_agent_model_turn"]["events"]),
        "new_events": result["new_events"], "output": str(args.output),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
