document.addEventListener('DOMContentLoaded', function() {
    // Doctor's initial greeting
    addMessage("Hello, I'm your virtual doctor. If you tell me about how you feel, I can help you with initial diagnosis.", "bot");
});

var symptomList = [];  // Global variable to store the symptom list

function addMessage(message, sender) {
    var chatContainer = document.getElementById('chat-container');
    var messageClass = sender === "user" ? "user-message" : "bot-message";
    var avatarClass = sender === "user" ? "user-avatar" : "doctor-avatar";

    var newMessage = document.createElement('div');
    newMessage.className = 'message ' + messageClass;
    newMessage.innerHTML = '<div class="avatar ' + avatarClass + '"></div>' +
                           '<div class="message-text">' + message + '</div>';

    chatContainer.appendChild(newMessage);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function sendMessage() {
    var userInput = document.getElementById('message-input').value.trim();
    if (!userInput) return;
    document.getElementById('message-input').value = '';

    addMessage(userInput, "user"); // Adding user (patient) message

    fetch('/get-response', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ patientInput: userInput, symptomList: symptomList })
    })
    .then(response => response.json())
    .then(data => {
        processResponse(data.doctorResponse); // Process response as doctor's message
    })
    .catch((error) => {
        console.error('Error:', error);
        addMessage("Sorry, there was an error processing your request.", "bot"); // Error in doctor's bubble
    });
}

function processResponse(response) {
    if (response.startsWith("[")) {
        try {
            symptomList = JSON.parse(response);
            addMessage("Thanks for the information! Based on your description, your symptoms are the following: " + symptomList.join(", ") + ". Is that correct? Please let me know if I'm missing anything.", "bot");
        } catch (e) {
            console.error("Error parsing symptom list:", e);
            addMessage("Sorry, there was an error processing your response.", "bot");
        }
    } else {
        addMessage(response, "bot");
    }
}

document.getElementById('send-button').addEventListener('click', sendMessage);
document.getElementById('message-input').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        e.preventDefault(); 
        sendMessage();
    }
});