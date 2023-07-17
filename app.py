#!/usr/bin/env python
import json

import asyncio

import websockets


async def handler(websocket):
    async for message in websocket:
        print(message)

    return
    # this is also where you do connection error handling 
    while True:
        try:
            message = await websocket.recv()
        except websockets.ConnectionClosedOK:
            # if the client closes connection while I was waiting for a message
            # with `websocket.recv()` then this is considered fine and we error
            
            # adding the exception clears the log and lets us expose more meaningful errors
            print("connection closed :3")
            break

        # if successfully received a message
        print(message)


async def main():
    # serve takes in 3 arguments
    #   handler: coroutine that manages a connection, when a client connects the handler is called w/ connection as argument
    #   network interfaces : DONT KNOW
    #   port : what port to be listening on

    async with websockets.serve(handler, "", 8001):
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    asyncio.run(main())
