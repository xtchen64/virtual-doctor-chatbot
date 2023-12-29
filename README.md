# virtual-doctor-chatbot
**Authors:** Elaine Chen, Qingyang Xu

## Description
A virtual doctor chatbot that helps patients diagnose their diseases based on a speech-based conversation, leveraging technologies including:
- GPT 3.5
- Web-based UI
- Speech transcribing & generation
- Diagnosis with Embedding-Based Retrieval (EBR) of patient symptoms using ClinicalBERT

![Virtual Doctor Chatbot Demo](https://github.com/xtchen64/virtual-doctor-chatbot/blob/main/resources/images/demo.gif)

![Virtual Doctor Product Design](https://github.com/xtchen64/virtual-doctor-chatbot/blob/main/resources/images/virtual_doctor_design.png)

## Setup
Note that the environment does not use brew or conda.

1. Set up local virtual environment (vscode only). This sets up a venv in the project folder:
  - In vscode terminal, make sure you are in the project folder. Create venv by running `python -m venv chatbot`
  - In vscode, if not prompted to do so, run `command+shift+p`, choose the chatbot interpreter
  - Activate this venv in terminal: `source chatbot/bin/activate`
2. Install required packages in terminal: `pip install -e .`
3. [Optional] For audio recording only. Install brew with `/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)`. Then run `brew install ffmpeg`. Note that this package can only be installed via brew.

## Guidance
- Please add a `config.py` file with one line: `OPENAI_API_KEY = 'your_openai_api_key_here'`
- To run the website demo, please run `python website/app.py`.

## Resources
- ChatDoctor Repo ([link](https://github.com/Kent0n-Li/ChatDoctor))
- Autonomous ChatDoctor with Disease Database ([link](https://huggingface.co/spaces/kenton-li/chatdoctor_csv)) - list of diseases, symptoms, medical tests, and medications
