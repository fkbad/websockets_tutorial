function myFunction() {
  // Get the text field
  var copyText = document.getElementById("myInput");

  // Select the text field
  copyText.select();
  copyText.setSelectionRange(0, 99999); // For mobile devices

  // Copy the text inside the text field
  navigator.clipboard.writeText(copyText.value);
  
  // Alert the copied text
  alert("Copied the text: " + copyText.value);
}


// HELPERS
function please_copy_join_link() {
  console.log("copy called!")
  // Get the text field
  let copyText = document.querySelector(".join").href;
  //
  updateClipboard(copyText)
}

function please_copy_watch_link() {
  console.log("copy watch called!")
  // Get the text field
  let copyText = document.querySelector(".watch").href;
  //
  updateClipboard(copyText)
}




function updateClipboard(newClip) {
  navigator.clipboard.writeText(newClip).then(
    () => {
      /* clipboard successfully set */
      console.log("shoulda copied [",newClip,"] to clipboard")
    },
    () => {
      /* clipboard write failed */
      console.log("couldn't write",newClip,"] to clipboard")
    },
  );
}

