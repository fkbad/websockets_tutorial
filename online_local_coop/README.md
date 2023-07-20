# Online Local-network Coop
## Quick Reference

{
    "type": "init"
}
{
    "type": "init",
	"join": "abDVjw"
}
{
    "type": "init",
	"watch": "wohgA"
}
{
    "type": "error",
	"message": "This slot is full."
}
{
	"type": "play"
	"player": "red"
	"column": 3
}
{
    "type": "play",
	"player": "red",
	"column": 3,
	"row": 0
}
{
    "type": "win",
	"player": "red"
}

---
{ "type": "init" }
{ "type": "init", "join": "abDVjw" }
{ "type": "init", "watch": "wohgA" }
{ "type": "error", "message": "This slot is full." }
{ "type": "play" "player": "red" "column": 3 }
{ "type": "play", "player": "red", "column": 3, "row": 0 }
{ "type": "win", "player": "red" }


## Event Types
### from the browser only:
- `{type: "play", player: "red", column: 3}`
    - player only drops in a column

- `{type: "init"}`
    - player one send this when the open a connection at `localhost:8000`, parsed in `handler()` in `app.py` to create match

- `{type: "init", join: "abDVjw"}`
    - when navigating to a join link provided by player 1, player2 will send this message to the server, parsed to send them to `join()` in `app.py`

- `{type: "init", watch: "wohgA"}`
    - when a player navigates to to the watch page of a game, this message will be sent
    to the server to say that someone has joined to watch on key `watch:` 

### from the server only:
- `{type: "init", join: "abDVjw", watch: "woaGH}`
    - sent by the server once a game has been created
        - this is so the frontend can generate the links to both join and watch a game

- `{type: "error", message: "This slot is full."}` 
    - generic error message, second field can be any string

- `{type: "play", player: "red", column: 3, row: 0}`
    - server response after parsing a valid move, adds in the row that a player's piece will fall too
- `{type: "win", player: "red"}`
    - winning message, sent whenever game logic knows the game is over

