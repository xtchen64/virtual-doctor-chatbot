document.addEventListener('DOMContentLoaded', function() {
    // Start the session automatically
    startSession();
});

function startSession() {
    // Make an API call to get the initial greeting
    fetch('/get-response', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text: "start_session" }) // Example text to initiate the session
    })
    .then(response => response.json())
    .then(data => {
        // Display the response from the server (initial greeting)
        addMessage(data.message, "bot");
    })
    .catch((error) => {
        console.error('Error:', error);
        addMessage("Sorry, there was an error starting the session.", "bot");
    });
}

function addMessage(message, sender) {
    var chatContainer = document.getElementById('chat-container');
    var messageClass = sender === "user" ? "user-message" : "bot-message";
    var avatarClass = sender === "user" ? "user-avatar" : "doctor-avatar";

    // Get the current timestamp
    var timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    // Create a new div for the message
    var newMessage = document.createElement('div');
    newMessage.className = 'message ' + messageClass;
    newMessage.innerHTML = 
        '<div class="avatar ' + avatarClass + '"></div>' +
        '<div class="message-wrapper">' +
            '<div class="timestamp">' + timestamp + '</div>' +
            '<div class="message-text">' + message + '</div>' +
        '</div>';

    // Append the new message div to the chat container
    chatContainer.appendChild(newMessage);

    // Scroll to the bottom of the chat container
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function sendMessage() {
    var userInput = document.getElementById('message-input').value.trim();
    if (!userInput) return; // Prevent sending empty messages
    document.getElementById('message-input').value = '';

    // Add the user's message to the chat
    addMessage(userInput, "user");

    // Send the user's input to the server and get a response
    fetch('/get-response', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text: userInput })
    })
    .then(response => response.json())
    .then(data => {
        // Display the response from the server
        addMessage(data.message, "bot");

        // Check if the session has ended
        if (!data.active_session) {
            // Display a session-end message or UI element
            displaySessionEndUI();
        }
    })
}

function displaySessionEndUI() {
    // Example: Display a session-end message
    var chatContainer = document.getElementById('chat-container');
    var sessionEndMessage = document.createElement('div');
    sessionEndMessage.className = 'session-end-message';
    sessionEndMessage.textContent = "This session has ended. Thank you for using the virtual doctor!";
    chatContainer.appendChild(sessionEndMessage);

    // Optionally, disable the input area
    document.getElementById('message-input').disabled = true;
    document.getElementById('send-button').disabled = true;
}

// Event listeners for sending a message
document.getElementById('send-button').addEventListener('click', sendMessage);
document.getElementById('message-input').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        e.preventDefault(); // Prevent the default form submit
        sendMessage();
    }
});