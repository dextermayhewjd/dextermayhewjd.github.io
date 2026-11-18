import asyncio


def record(events, name):
    events.append(name)  # 真正的动作是修改列表；这个回调不依靠返回值交付结果。


async def exercise():
    loop = asyncio.get_running_loop()
    events = []

    handle = loop.call_soon(record, events, "cancelled")  # 登记一次 record(events, "cancelled")。
    handle.cancel()  # 回调尚未执行，取消这一份登记。
    loop.call_soon(record, events, "kept")  # 另一次登记不取消，稍后会修改列表。

    print("before", events)  # 尚未交还执行机会，两次回调都没有运行。
    await asyncio.sleep(0)  # 循环跳过被取消的回调，执行保留的那一个。
    print("after", events)
    print("cancelled", handle.cancelled())  # True 表示这份 Handle 已被取消。


if __name__ == "__main__":
    asyncio.run(exercise())
