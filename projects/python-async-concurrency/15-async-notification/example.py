"""Event notifications and task mutual exclusion; Python 3.11+."""

import asyncio


async def main():
    # Keep the entered/release handshake and fetch(count) from Slime's test.
    entered, release = asyncio.Event(), asyncio.Event()
    group = ["sample"]

    async def fetch(count):
        entered.set()
        await release.wait()
        return [group][:count]

    print("initial", release.is_set())
    task = asyncio.create_task(fetch(1))
    await entered.wait()
    print("waiting", not task.done())
    release.set()
    release.set()  # Two notifications still leave only one True flag.
    print("set", release.is_set())
    print("received", await task)
    print("wait again", await release.wait())

    release.clear()
    entered.clear()
    print("cleared", release.is_set())
    task = asyncio.create_task(fetch(1))
    await entered.wait()
    print("waiting again", not task.done())
    release.set()
    await task

    # A separate API experiment: hold a lock while a known task requests it.
    update_lock = asyncio.Lock()
    requested = asyncio.Event()
    update_state = {"updating_model_path": None}

    async def update_from_disk(request):
        requested.set()
        async with update_lock:
            update_state["updating_model_path"] = request["model_path"]
        return update_state["updating_model_path"]

    await update_lock.acquire()
    try:
        task = asyncio.create_task(update_from_disk({"model_path": "checkpoint-2"}))
        await requested.wait()
        print("lock held", update_lock.locked())
        print("update waiting", not task.done())
    finally:
        update_lock.release()
    print("updated", await task)
    print("lock released", update_lock.locked())


if __name__ == "__main__":
    asyncio.run(main())
