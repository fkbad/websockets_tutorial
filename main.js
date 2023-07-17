import { createBoard, playMove } from "./connect4.js";

// overall initializer, the bootstrap or "main"
window.addEventListener("DOMContentLoaded", () => {
  // Initialize the UI.
  const board = document.querySelector(".board");
  createBoard(board);

  // Open the WebSocket connection and register event handlers.
  // port specified in main() of `app.py`
  const websocket = new WebSocket("ws://localhost:8001/");

  // this calls the sendMoves function which inside has the
  // click event listener. By calling it here in the setup 
  //     (which is setup because this is what `index.html` calls to start scripting)
  // this then adds the event listener to my website, which means
  // we can now start listening to clicks

  // think of it as sendMoves from browser
  sendMoves(board, websocket);

  // set up listener for messages being send from the website
  // think of it as recieveMoves from browser
  receiveMoves(board,websocket)
});

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

function receiveMoves(board, websocket) {
  websocket.addEventListener("message", ({ data }) => {
    const event = JSON.parse(data);
    switch (event.type) {
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
