document.getElementById('send-button').addEventListener('click', function() {
    var userInput = document.getElementById('message-input').value;
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
});