from flask import Flask, render_template, request, jsonify
import openai
from openai import OpenAI

app = Flask(__name__)

# Replace 'your_openai_api_key' with your actual OpenAI API key
openai.api_key = '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'
# Set up client
client = OpenAI(
    # defaults to os.environ.get("OPENAI_API_KEY")
    api_key=openai.api_key,
)


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
  1) If the patient provided any symptoms in the text, summarize the the symptoms in a Python list, for example: ['headache','toothache']. Do not say anything else besides this list.
  2) If the patient did not provide any symptoms in the text, then do not respond with a list. Instead, respond to their message in conversation-style sentences, and then tell the patient politely that you did not hear any symptoms and ask the patient to provide their symptoms. Do not respond with a list in this scenario.
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
      4) if the patient only says they want to add/revise the symptoms without providing enough information on the symptoms per se, then do not respond with a list. Instead, respond to their message in conversation-style sentences, and then politely ask the patient to provide more details or ask clarifying questions.
  """

  prompt_dict = {1: prompt1, 2: prompt2}
  prompt = prompt_dict[prompt_id]
  return prompt


def get_response(prompt, client):
  """
  Returns response from prompt.
  """
  response = client.chat.completions.create(
      messages=[
          {
              "role": "user",
              "content": prompt,
          }
      ],
      model="gpt-3.5-turbo",
  )

  message = response.choices[0].message.content

  return message

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get-response', methods=['POST'])
def handle_request():
    data = request.json
    user_text = data['text']

    # Generate the prompt
    prompt = get_prompt(user_text)

    # Get the response from OpenAI
    response_message = get_response(prompt, client)
    return jsonify({"message": response_message})

if __name__ == '__main__':
    app.run(debug=True)