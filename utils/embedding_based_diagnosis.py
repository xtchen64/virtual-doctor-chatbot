import numpy as np
import pandas as pd
import torch
from transformers import BertModel, BertTokenizer
from transformers import AutoTokenizer, AutoModel
import torch.nn.functional as F
import ast

"""
BERT embedding based disease diagnosis
- Use ClinicalBERT to embed each symptom string. Use the average embedding if there are multiple words in the string.
- For each symptom provided by the patient, find the maximum cosine similarity score with the symptoms of a disease.
- The patient-disease matching score (between 0 and 1) is the average cosine similarity score of all patient symptoms.
"""

VERBOSE = False

BERT_MODEL_ID = "medicalai/ClinicalBERT"
# BERT_MODEL_ID = "bert-base-uncased"

DISEASES_DF_PATH = "./resources/diagnosis/disease_diagnosis.csv"
DISEASES_DF = pd.read_csv(DISEASES_DF_PATH)
print(f"Found {DISEASES_DF.shape[0]} diseases")

print(f"Loading BERT model: {BERT_MODEL_ID}")

if BERT_MODEL_ID == "medicalai/ClinicalBERT":
    tokenizer = AutoTokenizer.from_pretrained("medicalai/ClinicalBERT")
    model = AutoModel.from_pretrained("medicalai/ClinicalBERT")
elif BERT_MODEL_ID == "bert-base-uncased":
    tokenizer = BertTokenizer.from_pretrained("bert-base-uncased")
    model = BertModel.from_pretrained("bert-base-uncased")
else:
    raise ValueError(f"Please input a valid BERT model ID {BERT_MODEL_ID}")

model.eval()
print(f"Loaded BERT model: {BERT_MODEL_ID}")

# Function to encode text to embeddings
def encode_text(text: str):
    inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=False)
    with torch.no_grad():
        outputs = model(**inputs)
    return outputs.last_hidden_state.mean(dim=1)


# Function to compute the average matching score between patient and disease symptoms
def compute_symptom_matching_score(patient_symptoms, disease_symptoms, verbose=False):

    if verbose:
        print(f"patient_symptoms: {patient_symptoms}")
        print(f"disease_symptoms: {disease_symptoms}")

    average_matching_score = 0

    disease_symptom_embeddings = torch.stack(
        [encode_text(symptom) for symptom in disease_symptoms]
    )

    for target_symptom in patient_symptoms:

        with torch.no_grad():
            target_embedding = encode_text(target_symptom)
            cosine_similarities = F.cosine_similarity(
                disease_symptom_embeddings.squeeze(), target_embedding
            )

        # Find the best match
        best_match_score = torch.max(cosine_similarities).numpy()

        if verbose:
            print(f"target_symptom: {target_symptom}")
            # Find the best match index
            best_match_index = torch.argmax(cosine_similarities).item()
            best_match_symptom = disease_symptoms[best_match_index]
            print(
                f"The symptom most similar to '{target_symptom}' is '{best_match_symptom}'."
            )
            print(f"Best Match Score: {best_match_score}")

        average_matching_score += best_match_score

    average_matching_score /= len(patient_symptoms)

    if verbose:
        print(f"average_matching_score: {average_matching_score}")

    return average_matching_score


# Function to find the best diagnosis to match patient symptoms
def find_best_diagnosis(patient_symptoms_str: str, verbose: bool = False):

    patient_symptoms = ast.literal_eval(patient_symptoms_str)

    if verbose:
        print(f"patient_symptoms: {patient_symptoms}")
        print(f"len(patient_symptoms): {len(patient_symptoms)}")

    max_matching_score = -np.inf
    best_diagnosis = None
    medications = None

    for ind in range(DISEASES_DF.shape[0]):
        disease = DISEASES_DF["disease"].iloc[ind]
        disease_symptoms_str = DISEASES_DF["symptoms"].iloc[ind]
        disease_symptoms = ast.literal_eval(disease_symptoms_str)
        average_matching_score = compute_symptom_matching_score(
            patient_symptoms, disease_symptoms, verbose=VERBOSE
        )
        if verbose:
            print(f"disease: {disease}")
            print(f"average_matching_score: {average_matching_score} \n")

        if average_matching_score > max_matching_score:
            max_matching_score = average_matching_score
            best_diagnosis = disease
            medications = DISEASES_DF["medications"].iloc[ind]

    if verbose:
        print(f"best_diagnosis: {best_diagnosis}")
        print(f"max_matching_score: {max_matching_score} \n")

    return best_diagnosis, max_matching_score, ast.literal_eval(medications)
