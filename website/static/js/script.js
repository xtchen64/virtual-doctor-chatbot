document.addEventListener('DOMContentLoaded', function() {
    // Initial greeting from the doctor when the page loads
    addMessage("Hello, I'm your virtual doctor. If you tell me about how you feel, I can help you with initial diagnosis.", "bot");
});

function addMessage(message, sender) {
    var chatContainer = document.getElementById('chat-container');
    var messageClass = sender === "user" ? "user-message" : "bot-message";
    var avatarClass = sender === "user" ? "user-avatar" : "doctor-avatar";

    // Create a new div for the message
    var newMessage = document.createElement('div');
    newMessage.className = 'message ' + messageClass;
    newMessage.innerHTML = '<div class="avatar ' + avatarClass + '"></div>' +
                           '<div class="message-text">' + message + '</div>';

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
    })
    .catch((error) => {
        console.error('Error:', error);
        addMessage("Sorry, there was an error processing your request.", "bot");
    });
}

// Event listeners for sending a message
document.getElementById('send-button').addEventListener('click', sendMessage);
document.getElementById('message-input').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        e.preventDefault(); // Prevent the default form submit
        sendMessage();
    }
});