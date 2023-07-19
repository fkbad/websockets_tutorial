import { createBoard, playMove } from "./connect4.js";

// overall initializer, the bootstrap or "main"
window.addEventListener("DOMContentLoaded", () => {
  // Initialize the UI.
  const board = document.querySelector(".board");
  createBoard(board);

  // Open the WebSocket connection and register event handlers.
  // port specified in main() of `app.py`
  const websocket = new WebSocket("ws://localhost:8001/");

  // adds listener to someone connecting
  initGame(websocket);

  // this calls the sendMoves function which inside has the
  // click event listener. By calling it here in the setup 
  //     (which is setup because this is what `index.html` calls to start scripting)
  // this then adds the event listener to my website, which means
  // we can now start listening to clicks

  // think of it as sendMoves from browser
  sendMoves(board, websocket);

  // set up listener for messages being send from the website
  // think of it as recieveMoves from browser
  recieveMessages(board,websocket)
});

function initGame(websocket) {

  //function to start a game upon the initialization of a websocket
  websocket.addEventListener("open", () => {
    /* 
     * when a connection is opened, it will either be the initializing player 
     * OR it will be a player joining a specific game from a link
     *
     * thus we need to parse the URL to see if there is anything in it related to the game*/

    // this returns a dictionary
    const url_params = new URLSearchParams(window.location.search)
    // search params uses dict-like get syntax
    // has separate method to check whether or not a field is in the URL
    const join_key = url_params.get("join")
    const watch_key = url_params.get("watch")
    if (join_key) {
      console.log("wow I have join field!")
    }
    // no matter what we are sending an event with init inside
    let event = {
      type: "init",
    }
    if (join_key) {
      // send link
      // specifically event with format:
      //  {type: "init", join: join_key}

      // printing with variables is good to use multiple args
      // since doing + concatentation won't print the content of 
      // larger structs apparently
      console.log("found join key", join_key, "in URL ")

      // add the join field to the event if we havea key
      event.join = join_key
    } else if (watch_key) {
      // tell the server that I have someone watching with this watch key
      event.watch = watch_key
    }
    else  { // link is just root
      // create new game
    }
    // send init message with join key filled in when necessary
    const jsoned_event = JSON.stringify(event)
    websocket.send(jsoned_event)
  });
}
// function to listen for clicks and send move information when 
// a click is on a column
function sendMoves(board, websocket) {
  // When clicking a column, send a "play" event for a move in that column.
  board.addEventListener("click", ({ target }) => {
    const column = target.dataset.column;
    // Ignore clicks outside a column.
    if (column === undefined) {
      return;
    }
    const event = {
      type: "play",
      column: parseInt(column, 10),
    };
    // send personally formatted JSON to server
    websocket.send(JSON.stringify(event));
  });
}

//
function showMessage(message) {
  // waits 50 ms before calling the alert
  // to make sure playMove() has finished running 
  // before ending
  window.setTimeout(() => window.alert(message), 50);
}

// since this is JS, this is the side of the website
// so when the website recieves a message from the server
// the event listener in here will get that message and process it
function recieveMessages(board, websocket) {
  websocket.addEventListener("message", ({ data }) => {
    const event = JSON.parse(data);
    console.log(event)
    switch (event.type) {
      case "init":
        // receiving init from the player/browser
        // means we want to start the next game!
        //
        // event.join is the join_key for the start of the game 
        // event.watch is the watch_key for the start of the game 
        //
        // adds the link with the join code appened to the join button
        document.querySelector(".join").href = "?join=" + event.join;
        document.querySelector(".watch").href = "?watch=" + event.watch;

        // break added because switch cases are fun :)
        break;

      case "play":
        // Update the UI with the move.
        playMove(board, event.player, event.column, event.row);
        break;

      case "win":
        showMessage(`Player ${event.player} wins!`);
        // No further messages are expected; close the WebSocket connection.
        websocket.close(1000);
        break;

      case "error":
        showMessage(event.message);
        break;

      default:
        throw new Error(`Unsupported event type: ${event.type}.`);
    }
  });
}
