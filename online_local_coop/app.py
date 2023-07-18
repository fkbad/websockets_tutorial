#!/usr/bin/env python
# for game id numbering
import secrets

import json

import asyncio

import websockets

from connect4 import PLAYER1, PLAYER2, Connect4

import logging
# logging.basicConfig(format="%(message)s", level=logging.DEBUG)

# module level dict to store all currently active games
# stored as { join key : (Connect4 Game Object, set of all connected websockets for that game) }
OPEN_MATCHES = {}


async def start_game(websocket):
    """
    part2 handler to create a game for the first time 
    """
    game = Connect4()
    connected_websockets = {websocket}

    # generates random url safe string with 5 bytes
    join_key = secrets.token_urlsafe(5)

    # log match in match dict
    OPEN_MATCHES[join_key] = game,connected_websockets

    try:
        await send_new_game(websocket,join_key=join_key)


        # keep grabbing messages
        print(f"game created with id = {id(join_key)}")
        async for message in websocket:
            print(message)

    finally:
        # deleting the entry in the open matches because 
        # when the connection is closed this game and the websocket data structure
        # are no longer valid, but will be kept in memory
        del OPEN_MATCHES[join_key]




async def send_new_game(websocket,join_key):
    """
    sends the initGame messgae with a join created upon the first player opening the websocket
    """
    event = {
            "type": "init",
            "join": join_key,
            }

    jsoned_event = json.dumps(event)
    print(f"sending jsoned_event : {jsoned_event}")
    await websocket.send(jsoned_event)

async def handler(websocket):
    # game creation is now UI based
    # we don't actually create a connection until we recieve 
    # a message saying that we want to start a game
    print(f"CALLED HANDLER")
    first_message = await websocket.recv()

    event = json.loads(first_message)
    print("event received", event)

    # should only ever recieve an opening connection message
    # from the beginning
    assert event["type"] == "init"

    # now we know we're starting a game, call on start and let it handle the event_loop
    await start_game(websocket)



# each handler is assocated with a websocket
# handler takes in a message from the browser game
# that message is only going to be a move
# {"type": "play", column: int}
# then we need to play that move on the board, get the response
# from the game, then send that information back over
async def old_part1_handler(websocket):

    game = Connect4()
    curr_player = PLAYER1

    # await test_sending(websocket,game=game)

    async for message in websocket:
        event = json.loads(message)
        event_type = event.get("type")

        if not event_type:
            raise ValueError("client should not be ever sending a message without a type")

        if event_type != "play":
            raise ValueError(f"client sent message with non-play type: {event_type}")

        column = event.get("column")
        if column is None:
            print(f"col val : {column}")
            raise ValueError(f"no column given")

        try:
            landing_row = game.play(curr_player,column) 
        except RuntimeError as exc:
            await send_error(websocket,error=exc)
            continue

        winner = game.winner

        await send_move(websocket,player=curr_player,row=landing_row,column=column)

        if winner:
            await send_winner(websocket,winner=winner)
        
        # swap players
        if curr_player == PLAYER1:
            curr_player = PLAYER2
        elif curr_player == PLAYER2:
            curr_player = PLAYER1


async def send_error(websocket,error):
    """
    sends the given error via the websocket

    type: "error"
    message: string
    """
    event = {
            "type": "error",
            "message": str(error) 
            }

    jsoned_event = json.dumps(event)
    await websocket.send(jsoned_event)

async def send_move(websocket,player,row,column):
    """
    after validating the row and column, sends a move with that coordinate
    for the particular player
    """

    event = {
            "type":"play",
            "player": player,
            "column": column,
            "row": row
            }
    jsoned_event = json.dumps(event)
    await websocket.send(jsoned_event)

async def send_winner(websocket,winner):
    """
    sends a correctly formatted event for the winner winning in a game of connect 4

    inputs:
        websocket to send message through
        winner: string of the color of the winning player, provided by Connect4.winner
    """
    # winning message, game is over
    # sending message of type "win", with player color
    event = {
            "type": "win",
            "player": winner
            }

    # not sure what the difference is here between json.dump and json.dumps
    jsoned_event = json.dumps(event)
    print(f"we got a winner :)", jsoned_event)
    await websocket.send(jsoned_event)


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

async def test_sending(websocket,game: Connect4):
    curr_player = PLAYER1
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
                "player": player,
                "type": "play",
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

    # # game is done
    # event = {
    #         "type": "win",
    #         "player": PLAYER1,
    #         }
    # jsoned_event = json.dumps(event)
    # await websocket.send(jsoned_event)
    # print("win!")

if __name__ == "__main__":
    asyncio.run(main())


