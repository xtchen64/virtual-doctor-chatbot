// Function to handle sending of message
function sendMessage() {
    var userInput = document.getElementById('message-input').value;
    if (!userInput.trim()) return; // Prevent sending empty messages
    document.getElementById('message-input').value = '';

    var chatContainer = document.getElementById('chat-container');

    // User's message with avatar
    chatContainer.innerHTML += '<div class="message user-message">' +
                               '<div class="avatar user-avatar"></div>' + userInput + '</div>';

    // Simulated bot response
    setTimeout(function() {
        var botResponse = "Hello, I'm your virtual doctor";
        chatContainer.innerHTML += '<div class="message bot-message">' +
                                   '<div class="avatar doctor-avatar"></div>' + botResponse + '</div>';
    }, 1000);
}

// Event listener for the Send button
document.getElementById('send-button').addEventListener('click', sendMessage);

// Event listener for the Enter key in the input field
document.getElementById('message-input').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        e.preventDefault(); // Prevent the default action to stop form submission
        sendMessage();
    }
});
