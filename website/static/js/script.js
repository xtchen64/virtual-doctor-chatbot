let currentAudio = null;

document.addEventListener('DOMContentLoaded', function() {
    startSession();
});

function startSession() {
    fetch('/get-response', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text: "start_session" })
    })
    .then(response => response.json())
    .then(data => {
        addMessage(data.message, "bot");
    })
    .catch((error) => {
        console.error('Error:', error);
        addMessage("Sorry, there was an error starting the session.", "bot");
    });
}

function addMessage(message, sender, audioFile = null) {
    var chatContainer = document.getElementById('chat-container');
    var messageClass = sender === "user" ? "user-message" : "bot-message";
    var avatarClass = sender === "user" ? "user-avatar" : "doctor-avatar";

    var timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    var newMessage = document.createElement('div');
    newMessage.className = 'message ' + messageClass;
    newMessage.innerHTML = 
        '<div class="avatar ' + avatarClass + '"></div>' +
        '<div class="message-wrapper">' +
            '<div class="timestamp">' + timestamp + '</div>' +
            '<div class="message-text">' + message + '</div>' +
        '</div>';

    chatContainer.appendChild(newMessage);
    chatContainer.scrollTop = chatContainer.scrollHeight;

    if (audioFile && sender === "bot") {
        playAudioResponse(audioFile);
    }
}

function playAudioResponse(audioSrc, onAudioEnd=null) {
    // Append a unique timestamp to the audio source URL
    const uniqueSrc = audioSrc + '?t=' + new Date().getTime();

    // Stop currently playing audio if there is one
    if (currentAudio && !currentAudio.ended) {
        currentAudio.pause();
        currentAudio.currentTime = 0; // Reset the playback position
    }

    // Start the new audio
    currentAudio = new Audio(uniqueSrc);
    currentAudio.play();

    // Call the callback function when audio ends
    if (onAudioEnd) {
        currentAudio.onended = onAudioEnd;
    }
}

function handleEndSession() {
    // Function to call the end-session API
    function endSessionAPI() {
        fetch('/end-session', {
            method: 'GET'
        })
        .then(response => response.json())
        .then(data => {
            console.log("Session ended:", data.message);
            endSessionUI();
        })
        .catch(error => {
            console.error('Error:', error);
        });
    }

    // Check if there's audio currently playing
    if (currentAudio && !currentAudio.ended) {
        // Wait for the audio to finish then call the end-session API
        playAudioResponse(currentAudio.src, endSessionAPI);
    } else {
        // No audio playing, call the end-session API immediately
        endSessionAPI();
    }
}

document.getElementById('send-button').addEventListener('click', function() {
    var userInput = document.getElementById('message-input').value.trim();
    if (userInput) {
        addMessage(userInput, "user");
        sendMessage(userInput);
        document.getElementById('message-input').value = '';
    }
});

document.getElementById('message-input').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        e.preventDefault();
        var userInput = document.getElementById('message-input').value.trim();
        if (userInput) {
            addMessage(userInput, "user");
            sendMessage(userInput);
            document.getElementById('message-input').value = '';
        }
    }
});

let isRecording = false;
let mediaRecorder;
let audioChunks = [];

const recordButton = document.getElementById('record-button');

recordButton.addEventListener('click', function() {
    if (isRecording) {
        stopRecording();
        recordButton.textContent = 'Record';
    } else {
        startRecording();
        recordButton.textContent = 'Stop';
    }
    isRecording = !isRecording;
});

function startRecording() {
    navigator.mediaDevices.getUserMedia({ audio: true })
        .then(stream => {
            mediaRecorder = new MediaRecorder(stream);
            mediaRecorder.start();

            audioChunks = [];
            mediaRecorder.addEventListener("dataavailable", event => {
                audioChunks.push(event.data);
            });

            mediaRecorder.addEventListener("stop", () => {
                const audioBlob = new Blob(audioChunks, { type: 'audio/mpeg' });
                sendAudioToServer(audioBlob);
            });
        })
        .catch(error => {
            console.error('Error accessing media devices:', error);
        });
}

function stopRecording() {
    mediaRecorder.stop();
}

function sendAudioToServer(audioBlob) {
    let formData = new FormData();
    formData.append("file", audioBlob, "recording.mp3");

    fetch('/voice-input', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.text) {
            addMessage(data.text, "user");
            sendMessage(data.text);
        } else if (data.error) {
            addMessage("Error: " + data.error, "bot");
        }
    })
    .catch(error => {
        console.error('Error:', error);
        addMessage("Sorry, there was an error processing your audio.", "bot");
    });
}

function sendMessage(userInput) {
    fetch('/get-response', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text: userInput })
    })
    .then(response => response.json())
    .then(data => {
        addMessage(data.message, "bot", data.audio_file);
        if (!data.active_session) {
            handleEndSession();
        }
    })
    .catch((error) => {
        console.error('Error:', error);
        addMessage("Sorry, there was an error processing your message.", "bot");
    });
}

function endSessionUI() {
    // Disable input and buttons
    document.getElementById('message-input').disabled = true;
    let sendButton = document.getElementById('send-button');
    let recordButton = document.getElementById('record-button');

    sendButton.disabled = true;
    recordButton.disabled = true;

    // Add a class to grey out the buttons
    sendButton.classList.add('disabled-button');
    recordButton.classList.add('disabled-button');

    // Create and add the end-of-session message
    var chatContainer = document.getElementById('chat-container');
    var endSessionMessage = document.createElement('div');
    endSessionMessage.className = 'end-session-message';
    endSessionMessage.textContent = "This chat has ended. Thank you!";

    chatContainer.appendChild(endSessionMessage);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function endSession() {
    fetch('/end-session', {
        method: 'GET'
    })
    .then(response => response.json())
    .then(data => {
        console.log("Session ended:", data.message);
        endSessionUI();
    })
    .catch(error => {
        console.error('Error:', error);
    });
}