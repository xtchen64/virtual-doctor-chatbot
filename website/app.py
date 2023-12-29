from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
import openai
from openai import OpenAI
from config import OPENAI_API_KEY
import speech_recognition as sr
import subprocess
from gtts import gTTS
import os
from utils.embedding_based_diagnosis import find_best_diagnosis


app = Flask(__name__)
CORS(app)  # Enable CORS

openai.api_key = OPENAI_API_KEY

client = OpenAI(api_key=openai.api_key)

# Global variables
prompt_id = 1
symptom_list_str = ""
active_session = True

def get_prompt(text: str, prompt_id=1, symptom_list_str=""):
  """
  Define prompts here.
  """
  # Prompt 1: Determine if answer contains symptoms:
  # - if yes, process potential symptoms into a list
  # - if not, ask user to provide symptoms
  prompt1 = f""" Imagine you are a professional medical doctor and speaking with a patient. \
  The conversation with the patient is in the text below, delimited by triple backticks. \
  ```{text}```

  Do one of the following, whichever is better:
  1) If the patient provided any medical symptoms in the text, summarize the the medical symptoms in a Python list, for example: ['headache','toothache']. Do not say anything else besides this list. Note that irrelevant words such as greeting-related text are not symptoms - please use your medical expertise to make the judgement. Do not hallucinate symptoms that are not in the text.
  2) If the patient did not provide any medical symptoms in the text, then do not respond with a list. Instead, respond to their message in conversation-style sentences, and then tell the patient politely that you did not hear any symptoms and ask the patient to provide their symptoms. Do not respond with a list in this scenario.
  """

  # Prompt 2: Determine if the patient says the symptom list looks good:
  # - if yes, answer one word ("proceed") only
  # - if no, 
  #     1) if the patient wants to add/remove any symptom, then add/remove the symptom in the original symptom list, and return the symptom list, for example: ['headache','toothache','chest pain'].
  #     2) if the patient wants to modify the symptom list, then revise accordingly (you can add/remove/modify symptoms), and return the revised symptom list, for example, ['headache','severe toothache']
  #     3) if the patient only says they want to add/revise the symptoms without providing enough information on the symptoms per se, then politely ask the patient to provide more details or ask clarifying questions.

  prompt2 = f""" Imagine you are a professional medical doctor and speaking with a patient. \
  You have previously asked a question to confirm the list of symptoms that the patient has provided.\
  The question we asked the patient was: 'Based on our conversation, these are your symptoms: {symptom_list_str}. Is there anything that you want to add or clarify?'
  The response by the patient is in the text below, delimited by triple backticks. \
  ```{text}```

  The current symptom list we are confirming is: {symptom_list_str}.
  Please determine if the patient says the symptom list looks good:
  If the patient's response indicates that the symptom list looks good or if there is nothing to modify in the list, answer one word ("proceed") only. Do not say anything else besides the word.
  If the patient's response indicates that the symptom list does not look good, do one of the following, whichever is the most suitable:
      1) if the patient wants to add/remove any symptom, then add/remove the symptom in the original symptom list, and return the symptom list, for example: ['headache','toothache','chest pain']. Do not say anything else besides this list.
      2) if the patient wants to modify the symptom list, then add any new symptoms captured, and revise the existing list accordingly (you can remove/modify symptoms), and return the revised symptom list, for example, ['headache','severe toothache'] Do not say anything else besides this list.
      3) if it seems that the patient has more symptoms than there are in the list, then do not respond with a list. Instead, respond to their message in conversation-style sentences, encourage them to share more about their symptoms.
      4) if the patient shows any hesitation (e.g. "not sure" or "hmm"), or only says they want to add/revise the symptoms without providing enough information on the symptoms per se, then do not respond with a list. Instead, address the patient by comforting them, and then politely ask the patient to provide more details or ask clarifying questions.
  """

  prompt_dict = {1: prompt1, 2: prompt2}
  prompt = prompt_dict[prompt_id]
  return prompt


def cleanup_temp_data():
    """
    Remove temp data.
    """
    audio_file_path = 'website/doctor_response.mp3'
    if os.path.exists(audio_file_path):
        os.remove(audio_file_path)
        print("Audio file removed successfully")


# TODO: Implement embedding-based retrieval to get diagnosis from symptoms
def get_response(prompt, client):
    """
    Returns response from prompt.
    """
    try:
        response = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model="gpt-3.5-turbo",
        )
    except Exception as e:
        print(f"An error occurred: {e}")

    message = response.choices[0].message.content

    return message

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/voice-input', methods=['POST'])
def handle_voice_input():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'})

    audio_file = request.files['file']
    original_audio_path = "temp_audio_original.webm"  # Assuming the file is in WebM format
    converted_audio_path = "temp_audio_converted.wav"  # Target WAV format
    audio_file.save(original_audio_path)

    # Use FFmpeg to convert the audio file to PCM WAV format
    try:
        subprocess.run(["ffmpeg", "-i", original_audio_path, converted_audio_path])
    except Exception as e:
        return jsonify({'error': str(e)})

    # Now process the converted file with speech_recognition
    recognizer = sr.Recognizer()
    with sr.AudioFile(converted_audio_path) as source:
        audio_data = recognizer.record(source)
        try:
            text = recognizer.recognize_google(audio_data)
        except sr.UnknownValueError:
            text = "Speech recognition could not understand audio"
        except sr.RequestError as e:
            text = "Could not request results from speech recognition service; {0}".format(e)

    # Clean up: remove temporary files
    os.remove(original_audio_path)
    os.remove(converted_audio_path)

    return jsonify({'text': text})

@app.route('/get-response', methods=['POST'])
def handle_request():
    # Declare global variables
    global prompt_id, symptom_list_str, active_session  # Declare global variables

    data = request.json
    user_text = data['text']

    """
    Generate doctor_response
    1. prompt_id == 1 => get prompt => get doctor_raw_response.
        a. if doctor_raw_response starts with "[" => Update symptom_list_str and set prompt_id to 2 => doctor_confirm_response
        b. else => directly return doctor_raw_response
    2. prompt_id == 2 => get prompt => get doctor_raw_response.
        a. if doctor_raw_response == "proceed" => return doctor_final_words => end session
        b. if doctor_raw_response starts with "[" => Update symptom_list_str with doctor_raw_response => doctor_confirm_response
        b. else => return doctor_raw_response
    """
    if user_text == "start_session":
        doctor_response = "Hello, I'm your virtual doctor. How can I assist you today?"
        active_session = True
    else:
        prompt = get_prompt(user_text, prompt_id, symptom_list_str)
        doctor_raw_response = get_response(prompt, client)
        
        if prompt_id == 1:
            if doctor_raw_response.startswith("["):
                symptom_list_str = doctor_raw_response  # Update the global variable
                prompt_id = 2
                doctor_response = 'Based on our conversation, these are your symptoms: {}. Is there anything that you want to add or clarify?'.format(symptom_list_str.replace("'","")[1:-1])
            else:
                doctor_response = doctor_raw_response
        
        elif prompt_id == 2:
            if doctor_raw_response == "proceed":
                diagnosis, score, medications = find_best_diagnosis(symptom_list_str, verbose=True)
                doctor_response = "Thank you for your patience! Based on your symptoms, the most likely diagnosis is [{}] (with {}% confidence). \
                The suggested medications are {}. \
                Hope you feel better soon! Good bye!".format(diagnosis.lower(), int(score*100), ", ".join(medications))
                active_session = False

            elif doctor_raw_response.startswith("["):
                symptom_list_str = doctor_raw_response  # Update the global variable
                doctor_response = 'Based on our conversation, these are your symptoms: {}. Is there anything that you want to add or clarify?'.format(symptom_list_str.replace("'","")[1:-1])
            else:
                doctor_response = doctor_raw_response

        else:
            raise ValueError(f"Invalid prompt_id: {prompt_id}")

    response_data = {"message": doctor_response, "active_session": active_session}

    # Text to Speech conversion
    tts = gTTS(doctor_response, lang='en')
    audio_file_path = 'website/doctor_response.mp3'
    if os.path.exists(audio_file_path):
        os.remove(audio_file_path)
    tts.save(audio_file_path)

    response_data = {
        "message": doctor_response, 
        "active_session": active_session,
        "audio_file": '/doctor-response'  # Provide the endpoint to access the audio file
    }

    return jsonify(response_data)

@app.route('/doctor-response', methods=['GET'])
def get_audio_response():
    return send_file('doctor_response.mp3', as_attachment=True, mimetype='audio/mpeg')

@app.route('/end-session', methods=['GET', 'POST'])
def end_session():
    global active_session
    active_session = False
    cleanup_temp_data()
    return jsonify({"message": "Session ended and temp folder cleaned up"})

if __name__ == '__main__':
    app.run(debug=True)