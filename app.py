#!/usr/bin/env python
import json

import asyncio

import websockets

from connect4 import PLAYER1, PLAYER2

import logging
logging.basicConfig(format="%(message)s", level=logging.DEBUG)

# each handler is assocated with a websocket
async def handler(websocket):
    # run tests
    await test_sending(websocket)

    async for message in websocket:
        print(message)

async def old_handler(websocket):
    # syntax to print all messages
    # also does ConnectionClosedOK handling (silences it)
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

async def test_sending(websocket):
    for index,(player, column, row) in enumerate([
    (PLAYER1, 3, 0),
    (PLAYER2, 3, 1),
    (PLAYER1, 4, 0),
    (PLAYER2, 4, 1),
    (PLAYER1, 2, 0),
    (PLAYER2, 1, 0),
    (PLAYER1, 5, 0),
    ]):
        # define my event:
        event = {
                "type": "play",
                "player": player,
                "column": column,
                "row": row
                }
        jsoned_event = json.dumps(event)
        print(f"sent : {index} ")
        await websocket.send(jsoned_event)
        # sleep half a second
        interval = .01
        await asyncio.sleep(interval)
    print("done!")

    # game is done
    event = {
            "type": "win",
            "player": PLAYER1,
            }
    jsoned_event = json.dumps(event)
    await websocket.send(jsoned_event)
    print("win!")

if __name__ == "__main__":
    asyncio.run(main())


