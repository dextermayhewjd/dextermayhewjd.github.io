"""Cut down from tests/test_server_control.py: local TCP, no HTTP client."""
import asyncio


async def exercise():
    reports = asyncio.Queue()

    async def serve(reader, writer):
        report = None
        try:
            headers = await reader.readuntil(b'\r\n\r\n')
            length = int(headers.split(b'\r\n', 1)[0])
            body = await reader.readexactly(length)
            suffix = await reader.read(1)
            writer.write(b'echo\n' + body)
            await writer.drain()
            report = ('complete', body, suffix)
        except asyncio.IncompleteReadError as error:
            report = ('incomplete', error.partial, error.expected)
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            finally:
                reports.put_nowait(report)

    server = await asyncio.start_server(serve, '127.0.0.1', 0)
    port = server.sockets[0].getsockname()[1]
    print('server listening', server.is_serving())
    try:
        reader, writer = await asyncio.open_connection('127.0.0.1', port)
        try:
            writer.write(b'3\r\n\r\nabc!')
            await writer.drain()
            print('reply line', (await reader.readline()).decode().strip())
            print('reply body', await reader.read())
        finally:
            writer.close()
            await writer.wait_closed()
        print('handler', await reports.get())

        reader, writer = await asyncio.open_connection('127.0.0.1', port)
        writer.write(b'5\r\n\r\nxy')
        await writer.drain()
        writer.close()
        await writer.wait_closed()
        print('handler', await reports.get())
    finally:
        server.close()
        await server.wait_closed()
    print('server listening', server.is_serving())


if __name__ == '__main__':
    asyncio.run(exercise())
