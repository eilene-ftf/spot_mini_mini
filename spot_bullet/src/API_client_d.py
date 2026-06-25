import socket
import asyncio
import aiofiles
import os

DOG_HOST = "0.0.0.0"   # replace with dog/container IP
PORT_FROM_DOG = 65432     # dog streams sensor data to us on this port
PORT_TO_DOG   = 23456     # we push Bend output to dog on this port

FIFO_TO_BEND = "/tmp/api_outbox"    # Python writes, Bend reads
FIFO_FROM_BEND = "/tmp/api_inbox"   # Bend writes, Python reads

for path in (FIFO_TO_BEND, FIFO_FROM_BEND):
    if os.path.exists(path):
        os.remove(path)
    os.mkfifo(path)

async def forward_to_server(IP, PORT):
    while True:
        reader, writer = await asyncio.open_connection(
            IP, 
            PORT
        )
    
        async with aiofiles.open(FIFO_FROM_BEND, "r") as f:
            stream = ""
            async for line in f:
                stream += line

        print(f'Send: {stream!r}')
        if stream[:4] == "quit":
            writer.close()
            await writer.wait_closed()
            break

        writer.write(stream.encode())
        await writer.drain()

        print('Close the connection')
        writer.close()
        await writer.wait_closed()

async def forward_from_server(IP, PORT):
    while True:
        reader, writer = await asyncio.open_connection(
            IP, 
            PORT
        )

        data = await reader.read(100)
        print(f'Received: {data.decode()!r}')
        
        if data.decode()[:4] == "quit":
            writer.close()
            await writer.wait_closed()
            break

        async with aiofiles.open(FIFO_TO_BEND, "w") as f:
            await f.write(data.decode())
            await f.flush()
    
        print('Close the connection')
        writer.close()


async def main():
    try:
        await asyncio.gather(
            forward_to_server(DOG_HOST, PORT_TO_DOG),
            forward_from_server(DOG_HOST, PORT_FROM_DOG),
            #tcp_echo_client('Hello World from bend!', DOG_HOST, PORT_TO_DOG)
        )
    except (KeyboardInterrupt, AssertionError):
        print("Interrupted. Exiting.")

asyncio.run(main())
