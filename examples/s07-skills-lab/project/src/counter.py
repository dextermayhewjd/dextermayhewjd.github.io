import asyncio

async def increment(state):
    """Two completed increments must add two, including concurrent calls."""
    await asyncio.sleep(0)
    state["count"] += 1
