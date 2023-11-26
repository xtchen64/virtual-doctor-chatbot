from flask import Flask, render_template, request, jsonify
import openai
from openai import OpenAI
from config import OPENAI_API_KEY

app = Flask(__name__)

# Replace 'your_openai_api_key' with your actual OpenAI API key
openai.api_key = OPENAI_API_KEY
# Set up client
client = OpenAI(
    # defaults to os.environ.get("OPENAI_API_KEY")
    api_key=openai.api_key,
)

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
                doctor_response = 'Based on our conversation, these are your symptoms: {}. Is there anything that you want to add or clarify?'.format(symptom_list_str)
            else:
                doctor_response = doctor_raw_response
        
        else:  # prompt_id == 2
            if doctor_raw_response == "proceed":
                doctor_response = "Thank you for using virtual doctor! Based on our conversation, these are your symptoms: {}. Good bye!".format(symptom_list_str)
                active_session = False
            elif doctor_raw_response.startswith("["):
                symptom_list_str = doctor_raw_response  # Update the global variable
                doctor_response = 'Based on our conversation, these are your symptoms: {}. Is there anything that you want to add or clarify?'.format(symptom_list_str)
            else:
                doctor_response = doctor_raw_response

    return jsonify({"message": doctor_response, "active_session": active_session})

if __name__ == '__main__':
    app.run(debug=True)