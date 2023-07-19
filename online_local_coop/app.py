#!/usr/bin/env python
# for game id numbering
import secrets

import json

import asyncio
from typing import Set, Tuple, List

import websockets

from connect4 import PLAYER1, PLAYER2, Connect4

import logging
# logging.basicConfig(format="%(message)s", level=logging.DEBUG)

# module level dict to store all currently active games
# stored as { join key : (Connect4 Game Object, set of all connected websockets for that game) }
# CURR_MATCHES: [str,Tuple[Connect4,websockets.__all__]] = {}
CURR_MATCHES = {}
# dict that stores a game object and all websockets that are 
# spectating that match
WATCHING_MATCHES = {}

# dict to track relationship between watch keys and join keys
WATCH_KEY_TO_JOIN_KEY = {}
JOIN_KEY_TO_WATCH_KEY = {}

JOIN_KEY_SIZE = 5

async def start_game(websocket):
    """
    part2 handler to create a game for the first time 
    """
    game = Connect4()
    connected_websockets = {websocket}

    # generates random url safe string with arguments' amount of bytes
    join_key = secrets.token_urlsafe(JOIN_KEY_SIZE)
    watch_key = secrets.token_urlsafe(JOIN_KEY_SIZE)

    CURR_MATCHES[join_key] = game,connected_websockets
    # empty set as the player who makes a game is meant to be player 1
    WATCHING_MATCHES[watch_key] = game,set()

    WATCH_KEY_TO_JOIN_KEY[watch_key] = join_key
    JOIN_KEY_TO_WATCH_KEY[join_key] = watch_key

    try:
        # send game information to frontend 
        await send_new_game(websocket,join_key=join_key,watch_key=watch_key)

        # player 1 starts playing
        await play(player_websocket=websocket,game=game,player=PLAYER1,connected_websockets=connected_websockets,game_watch_key=watch_key)
    finally:
        # deleting the entry in the open matches because 
        # when the connection is closed this game and the websocket data structure
        # are no longer valid, but will be kept in memory
        print(f"removing match with join_key:", join_key)
        del CURR_MATCHES[join_key]

        # if at any point this player disconnects, we want to also remove this game
        # from the watchable matches
        del WATCHING_MATCHES[watch_key]


async def watch(websocket, watch_key):
    """
    takes in a websocket connection that has a watch_key from the
    parsed URI.

    adds the websocket to the entry in WATCHING_MATCHES so it can be
    in the loop for game updates
    """

    game_socket_tuple = WATCHING_MATCHES.get(watch_key)

    if game_socket_tuple is None:
        await send_error(websocket,error=f"invalid watch key [{watch_key}] provided")
        return

    # else we have a valid watch key with an assocated game
    game,watching_websockets = game_socket_tuple

    watching_websockets.add(websocket)

    WATCHING_MATCHES[watch_key] = [game,watching_websockets]
    # TODO maybe change this out for something more comprehensive?
    async for message in websocket:
        print(f"\t spectator sent : {message}")

async def join(websocket, join_key):
    """
    this handles the event loop of the second player

    steps are:
        verify that the join_key is valid
        if so, then grab the game and list of websockets associated with that game

        update the entry in the CURR_MATCHES to include the websocket of the second playert
            (the one from function argument)

        once the connection has completed, remove the websocket from the set associated
        with the game
    """

    game_socket_tuple = CURR_MATCHES.get(join_key)

    if not game_socket_tuple:
        # invalid join key provided
        await send_error(websocket,error=f"invalid join key [{join_key}] provided")
        return
    
    # we know we have a valid game now, since .get returned a tuple
    game,connected_websockets = game_socket_tuple
    connected_websockets.add(websocket)

    CURR_MATCHES[join_key] = [game,connected_websockets]
    # grab the assocated watch jey to play can figure out 
    # which (if any) spectators to update
    watch_key = JOIN_KEY_TO_WATCH_KEY[join_key]

    assert(len(connected_websockets)==2)

    await play(player_websocket=websocket,game=game,player=PLAYER2,connected_websockets=connected_websockets,game_watch_key=watch_key)


    return 
    # connected_websockets.

async def play(player_websocket,game,player,connected_websockets,game_watch_key):
    """
    arbitrarily takes in a game, and a particular player
    then takes in any message from the player_websocket 
    and sees if it can happen based on Connect4 game logic

    if an action requiring an event happens (such as playing a move and/or ending the game)
    then that information will be sent to all websockets in the set of 
    "connected_websockets" associated with this game
    """
    async for message in player_websocket:
        event = json.loads(message)

        column = get_col_from_play_event(event)

        try:
            landing_row = game.play(player,column) 
        except RuntimeError as exc:
            # either the column is full or it is not your turn
            await send_error(player_websocket,error=exc)
            continue

        # if getting here, then no runtime errors occurred, 
        # thus we have a valid play from a player on their turn
        winner = game.winner
        await send_move(connected_websockets,player=player,row=landing_row,column=column,game_watch_key=game_watch_key)

        if winner:
            await send_winner(connected_websockets,winner=winner,game_watch_key=game_watch_key)


async def handler(websocket):
    # game creation is now UI based
    # we don't actually create a connection until we recieve 
    # a message saying that we want to start a game
    first_message = await websocket.recv()

    event = json.loads(first_message)
    print("event received", event)

    # should only ever recieve an opening connection message
    # from the beginning
    assert event["type"] == "init"

    # now we check whehter there is a join key
    join_key = event.get("join")
    watch_key = event.get("watch")

    if join_key:
        print(f"joining...")
        # second player has joined, let's process it!
        await join(websocket, join_key=join_key)

    elif watch_key:
        # second player has joined, let's process it!
        print(f"watching...")
        await watch(websocket, watch_key=watch_key)
    else:
        # now we know we're starting a game, call on start and let it handle the event_loop
        print(f"starting...")
        await start_game(websocket)





# HELPER FUNCTIONS

def get_col_from_play_event(event) -> int:
    """
    parses an event

    if its a play, parse, error check, and return the column

    no need to check if the column is in bounds as the `main.js` playMove function
    has column and row bound checking 
    """

    event_type = event.get("type")

    if not event_type:
        raise ValueError("client should not be ever sending a message without a type")

    if event_type != "play":
        raise ValueError(f"client sent message with non-play type: {event_type}")

    column = event.get("column")

    if column is None:
        print(f"col val : {column}")
        raise ValueError(f"no column given")

    return column

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

async def send_move(connected_websockets,player,row,column,game_watch_key):
    """
    after validating the row and column, sends a move with that coordinate
    to all given websockets
    """

    event = {
            "type":"play",
            "player": player,
            "column": column,
            "row": row
            }
    jsoned_event = json.dumps(event)
    for websocket in connected_websockets:
        await websocket.send(jsoned_event)

    _,watching_websockets = WATCHING_MATCHES[game_watch_key]
    
    websockets.broadcast(watching_websockets,jsoned_event)

async def send_winner(connected_websockets,winner,game_watch_key):
    """
    sends a correctly formatted event for the winner winning in a game of connect 4

    inputs:
        set of websockets to send message to
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
    for websocket in connected_websockets:
        await websocket.send(jsoned_event)
    _,watching_websockets = WATCHING_MATCHES[game_watch_key]
    
    websockets.broadcast(watching_websockets,jsoned_event)

async def send_new_game(websocket,join_key,watch_key):
    """
    sends the initGame messgae with a join created upon the first player opening the websocket
    """
    event = {
            "type": "init",
            "join": join_key,
            "watch": watch_key
            }

    jsoned_event = json.dumps(event)
    print(f"sending event {jsoned_event}")
    await websocket.send(jsoned_event)

# END OF HELPER FUNCTIONS

# MAIN

async def main():
    # serve takes in 3 arguments
    #   handler: coroutine that manages a connection, when a client connects the handler is called w/ connection as argument
    #   network interfaces : DONT KNOW
    #   port : what port to be listening on

    async with websockets.serve(handler, "", 8001):
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())
