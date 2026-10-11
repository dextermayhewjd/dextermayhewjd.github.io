"""Execute unchanged source functions with recording dependencies, without SDK/CLI."""
from __future__ import annotations

import ast
import asyncio
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace


HERE = Path(__file__).resolve().parent
REPO = Path('/home/fredkeira/projects/slime')


class RecordingSandbox:
    def __init__(self, outcome, output):
        self.outcome = outcome
        self.output = output
        self.operations = []
        self.polls = 0

    async def write_file(self, path, content, *, user='root'):
        self.operations.append({'method': 'write_file', 'path': path, 'content': content, 'user': user})

    async def read_file(self, path, *, user='root'):
        self.operations.append({'method': 'read_file', 'path': path, 'user': user})
        return self.output

    async def exec(self, cmd, **kwargs):
        result = (0, '', '')
        if cmd.startswith('test -f '):
            self.polls += 1
            result = (1, '', '')
            if self.outcome is not None and self.polls >= 2:
                result = (0, str(self.outcome) + '\n', '')
        elif cmd.startswith('tail -c '):
            result = (0, self.output.encode()[-512:].decode(), '')
        self.operations.append({'method': 'exec', 'cmd': cmd, **kwargs, 'simulated_result': result})
        return result


def run_case(source, input_data, outcome, output, want_output=False, budget=1800):
    tree = ast.parse(source)
    selected = [node for node in tree.body if isinstance(node, ast.AsyncFunctionDef)
                and node.name in {'exec_and_wait', '_await_done_marker'}]
    assert len(selected) == 2
    elapsed = [0]
    sleeps = []

    async def fake_sleep(seconds):
        elapsed[0] += seconds
        sleeps.append(seconds)

    namespace = {
        'Sandbox': object, 'EXIT_TIME_BUDGET_EXCEEDED': -1,
        'time': SimpleNamespace(time=lambda: elapsed[0]),
        'asyncio': SimpleNamespace(sleep=fake_sleep),
    }
    module = ast.Module(body=[ast.ImportFrom(module='__future__', names=[ast.alias(name='annotations')], level=0),
                              *selected], type_ignores=[])
    exec(compile(ast.fix_missing_locations(module), str(REPO/'slime/agent/sandbox.py'), 'exec'), namespace)
    sb = RecordingSandbox(outcome, output)
    arguments = dict(cmd=input_data['start_cmd'], workdir=input_data['workdir'], user='agent',
                     env=input_data['env'], out_file=input_data['out_file'], tag='run',
                     time_budget_sec=budget, want_output=want_output)
    result = asyncio.run(namespace['exec_and_wait'](sb, **arguments))
    operations = sb.operations
    assert operations[0]['method'] == 'write_file'
    assert operations[0]['path'] == '/tmp/.run.sh'
    assert operations[0]['content'].endswith('echo $? > /tmp/.run.done\n')
    assert operations[1]['cmd'].startswith('rm -rf /tmp/.run.spawned; rm -f ')
    assert 'mkdir /tmp/.run.spawned' in operations[2]['cmd']
    assert 'setsid bash /tmp/.run.sh' in operations[2]['cmd']
    assert operations[2]['env'] == input_data['env']
    expected_code = -1 if outcome is None else outcome
    expected_output = output if want_output else ('' if expected_code == 0 else output.encode()[-512:].decode())
    assert result == (expected_code, expected_output), result
    return {'arguments': arguments, 'simulated_cli_exit': outcome,
            'operations': operations, 'simulated_sleep_seconds': sleeps,
            'return_value': result, 'passed': True}


def main():
    provenance = json.loads((HERE/'source-file-hashes.json').read_text())
    source_bytes = (REPO/'slime/agent/sandbox.py').read_bytes()
    assert hashlib.sha256(source_bytes).hexdigest() == provenance['slime/agent/sandbox.py']['sha256'], 'Source changed; rebind chapter evidence before running.'
    previous = json.loads((HERE.parents[2]/'4.Slime Core Components and Orchestration/4.1.Agent Rollout Adapters and Harnesses/5.Manage Sandbox/纵向数据流/示例.json').read_text())
    runner = previous['runner_input']
    input_data = {'workdir': runner['workdir'], 'start_cmd': runner['start_cmd'], 'env': runner['env'],
                  'out_file': runner['workdir'] + '/.harness/trajectory.jsonl'}
    source = source_bytes.decode()
    cases = {
        'success_without_output': run_case(source, input_data, 0, 'cli-complete\n'),
        'nonzero_exit_with_tail': run_case(source, input_data, 7, 'cli-error\n'),
        'explicit_full_output': run_case(source, input_data, 0, 'cli-complete\n', want_output=True),
        'wait_budget_exhausted': run_case(source, input_data, None, '', budget=10),
    }
    result = {
        'revision': '22a89f96835969a47055a659c588f46151f8b07a',
        'verification': {'mode': 'unchanged-source-AST-functions-with-recording-dependencies',
                         'executed_functions': ['exec_and_wait', '_await_done_marker'],
                         'simulated': ['Sandbox responses', 'sleep', 'wall clock', 'CLI output and exit values'],
                         'not_executed': ['E2B SDK', 'remote commands', 'CLI', 'model requests'],
                         'spawn_lock_semantics': 'statically reviewed; recording fake does not execute shell'},
        'input': input_data, 'cases': cases,
    }
    (HERE/'示例.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps({'controlled_cases_passed': len(cases), 'remote_execution': False}))


if __name__ == '__main__':
    main()
