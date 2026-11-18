"""Hook/trace teaching cuts plus independent async-protocol exercises."""
import asyncio
import functools
import inspect
from collections.abc import AsyncIterator, Awaitable
from contextlib import aclosing

EVENTS = []


def trace_function(name):
    # Slime keeps target resolution and trace_span here; we only record order.
    def decorator(fn):
        if inspect.iscoroutinefunction(fn):
            @functools.wraps(fn)
            async def async_wrapper(*args, **kwargs):
                EVENTS.append(name + ':enter')
                try:
                    return await fn(*args, **kwargs)
                finally:
                    EVENTS.append(name + ':exit')
            return async_wrapper

        @functools.wraps(fn)
        def sync_wrapper(*args, **kwargs):
            EVENTS.append(name + ':enter')
            try:
                return fn(*args, **kwargs)
            finally:
                EVENTS.append(name + ':exit')
        return sync_wrapper
    return decorator


@trace_function('sync')
def sync_hook(args, sample):
    return sample + 1


@trace_function('async')
async def async_hook(args, sample):
    await asyncio.sleep(0)
    return sample * 2


def deferred_hook(args, sample):
    return async_hook(args, sample)


HOOKS = {'sync': sync_hook, 'async': async_hook, 'deferred': deferred_hook}


async def _apply_to_sample(args, sample, paths, **kwargs):
    for path in paths:
        # Teaching substitution for Slime's load_function(path).
        hook = HOOKS[path]
        result = hook(args, sample, **kwargs)
        if inspect.isawaitable(result):
            result = await result
        if result is not None:
            sample = result
    return sample


class SampleStream:
    """Independent language exercise, not an excerpt from Slime."""
    def __init__(self):
        self.value = 0

    async def __aenter__(self):
        print('resource enter')
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        print('resource exit', exc_type.__name__ if exc_type else None)
        return False

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self.value == 2:
            raise StopAsyncIteration
        await asyncio.sleep(0)
        self.value += 1
        return self.value


async def chunks() -> AsyncIterator[int]:
    try:
        yield 10
        yield 20
    finally:
        print('generator closed')


async def exercise():
    result = await _apply_to_sample(None, 1, ['sync', 'async', 'deferred'])
    print('sample', result)
    print('trace', EVENTS)
    pending: Awaitable[int] = deferred_hook(None, 3)
    print('deferred', inspect.iscoroutinefunction(deferred_hook), inspect.isawaitable(pending))
    print('awaited', await pending)

    async with SampleStream() as stream:
        values = [value async for value in stream]
        print('values', values)

    stream: AsyncIterator[int] = chunks()
    async with aclosing(stream):
        async for value in stream:
            print('first', value)
            break


if __name__ == '__main__':
    asyncio.run(exercise())
