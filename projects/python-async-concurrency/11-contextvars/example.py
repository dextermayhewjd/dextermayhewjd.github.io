import asyncio
from contextlib import contextmanager
from contextvars import ContextVar

_task_rollout_id = ContextVar("rollout_sample_hook_id", default=None)

@contextmanager
def rollout_context(rollout_id):
    token = _task_rollout_id.set(rollout_id)
    try:
        yield
    finally:
        _task_rollout_id.reset(token)

async def generate(rollout_id):
    with rollout_context(rollout_id):
        await asyncio.sleep(0)
        return _task_rollout_id.get()

async def exercise():
    print("task values", await asyncio.gather(generate(10), generate(11)))
    print("outer value", _task_rollout_id.get())

if __name__ == "__main__":
    asyncio.run(exercise())
