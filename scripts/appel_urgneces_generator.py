# generate_emergency_calls.py
import vertexai
from vertexai.generative_models import GenerativeModel
import json
import os

# Configuration
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
vertexai.init(project=GCP_PROJECT_ID, location="europe-west1")
MODEL_NAME = "gemini-2.0-flash"
model = GenerativeModel(MODEL_NAME)

# Scénarios d'urgence
scenarios = [
    "Accident de voiture avec blessé conscient",
    "Personne âgée chute à domicile",
    "Enfant avec fièvre élevée et convulsions",
    "Douleur thoracique chez adulte 50 ans",
    "Saignement abondant suite coupure",
    "Difficulté respiratoire asthmatique",
    "Perte de connaissance brève",
    "Réaction allergique alimentaire",
    "Brûlure thermique étendue",
    "Traumatisme crânien suite chute"
]

def generate_call_transcript(scenario):
    prompt = f"""Génère un transcript RÉALISTE d'appel d'urgence au SAMU (15) en français.

SCÉNARIO: {scenario}

FORMAT REQUIS (JSON):
{{
  "scenario": "{scenario}",
  "caller_type": "témoin/victime/proche",
  "duration_seconds": 120-300,
  "transcript": [
    {{"speaker": "ARM", "text": "SAMU 15, j'écoute"}},
    {{"speaker": "Appelant", "text": "..."}},
    ...
  ],
  "urgency_level": "vital/très urgent/urgent/peu urgent",
  "symptoms": ["symptôme1", "symptôme2"],
  "actions_taken": ["action1", "action2"],
  "decision": "SMUR envoyé/Conseil médical/Orientation pompiers"
}}

CONSIGNES:
- Langage naturel avec hésitations ("euh", "je sais pas", répétitions)
- Durée réaliste (2-5 minutes = 15-30 échanges)
- Questions ARM structurées (ABCDE: Airways, Breathing, Circulation, Disability, Exposure)
- Stress de l'appelant apparent
- Détails médicaux précis

GÉNÈRE LE JSON COMPLET:"""

    try:
        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.8,
                "max_output_tokens": 2048,
            }
        )
        
        # Extraire JSON
        text = response.text
        json_start = text.find('{')
        json_end = text.rfind('}') + 1
        json_str = text[json_start:json_end]
        
        return json.loads(json_str)
    
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return None

# Génération du dataset
dataset = []
for i, scenario in enumerate(scenarios):
    print(f"🎬 Génération {i+1}/{len(scenarios)}: {scenario}")
    call = generate_call_transcript(scenario)
    if call:
        dataset.append(call)
    
    # Sauvegarder après chaque génération
    with open('emergency_calls_dataset.json', 'w', encoding='utf-8') as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)

print(f"✅ Dataset généré: {len(dataset)} appels")