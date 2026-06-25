import socket
import asyncio
# import aiofiles
import os

DOG_HOST = "0.0.0.0"   # replace with dog/container IP
PORT_FROM_DOG = 65432     # dog streams sensor data to us on this port
PORT_TO_DOG   = 23456     # we push Bend output to dog on this port

# Source - https://stackoverflow.com/a/53143060
# Posted by Vincent, modified by community. See post 'Timeline' for change history
# Retrieved 2026-06-23, License - CC BY-SA 4.0


async def handle_echo(reader, writer):
    data = await reader.read(100)
    message = data.decode()
    message_back  = data.decode() + '-- Server received.'
    addr = writer.get_extra_info('peername')

    print(f"Received {message!r} from {addr!r}")

    print(f"Send: {message_back!r}")
    writer.write(message_back.encode())
    await writer.drain()

    writer.close()
    await writer.wait_closed()

def yield_client_fn(data):
    dats = data[::-1]
    async def talk_to_client(reader, writer):
        nonlocal data
        print(f"data: {dats}")
        dat = dats.pop()
        print(f"Sending {dat}")
        writer.write(dat.encode())
        await writer.drain()
        print(f"Sent {dat}")

        writer.close()
        await writer.wait_closed()
    return talk_to_client

async def main():
    dummy_data = ["hello\n", "hi\n", "how are you?\n", "quit\n"]
    server1 = await asyncio.start_server(
        yield_client_fn(dummy_data), DOG_HOST, PORT_FROM_DOG)

    addr1 = server1.sockets[0].getsockname()
    print(f'Serving 1 on {addr1}')

    server2 = await asyncio.start_server(
        handle_echo, DOG_HOST, PORT_TO_DOG)

    addr2 = server2.sockets[0].getsockname()
    print(f'Serving 2 on {addr2}')

    async with server1, server2:
        await asyncio.gather(
            server1.serve_forever(), server2.serve_forever())

asyncio.run(main())
