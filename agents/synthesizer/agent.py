"""
Agent Synthétiseur ADK - ADN (AI Diagnostic Navigator)
'Le Double Cerveau' - Résume puis s'auto-critique pour trouver les incohérences
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from google import genai
from google.genai import types
from google.adk.agents import LlmAgent

from dotenv import load_dotenv
ENV_PATH = Path(__file__).parent.parent / ".env"  # agents/.env
load_dotenv(dotenv_path=ENV_PATH, override=True)

class AgentSynthetiseur:
    """
    Agent ADK qui synthétise les données patient et s'autocritique
    Compatible avec l'interface ADK et le format hospitalier/SAMU
    """

    def __init__(self):
        """Initialise l'agent avec le client Gemini"""
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.client = genai.Client(api_key=self.api_key)
        self.model_id = "gemini-2.0-flash-exp"
        
    def normaliser_input(self, data_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalise n'importe quel format d'input en format unifié
        Gère : format hospitalier, appels SAMU, ou tout autre format
        """
        # Si c'est déjà au bon format (patient_normalized existe)
        if "patient_normalized" in data_input:
            return data_input

        # Si c'est un appel SAMU (avec input.text et expected_output)
        if "input" in data_input and "expected_output" in data_input:
            return self._convertir_format_samu(data_input)

        # Sinon, essayer de détecter automatiquement
        return self._auto_detecter_format(data_input)

    def _convertir_format_samu(self, data_samu: Dict) -> Dict:
        """Convertit le format SAMU en format unifié"""
        expected = data_samu.get("expected_output", {})
        meta = data_samu.get("meta", {})
        appel_text = data_samu.get("input", {}).get("text", "")

        patient_normalized = {
            "id": data_samu.get("id", "SAMU_UNKNOWN"),
            "source_type": "SAMU_CALL",
            "call_transcript": appel_text,
            "scenario": meta.get("scenario", "Non spécifié"),
            "age": expected.get("patient_identification", {}).get("age"),
            "sex": expected.get("patient_identification", {}).get("sex"),
            "weight": expected.get("patient_identification", {}).get("weight"),
            "admission": {
                "type": "PREHOSPITAL_EMERGENCY",
                "chief_complaint": expected.get("incident_description", {}).get("main_reason"),
                "mechanism": expected.get("incident_description", {}).get("mechanism"),
                "onset_time": expected.get("incident_description", {}).get("onset_time"),
                "evolution": expected.get("incident_description", {}).get("evolution"),
                "date": None
            },
            "location": expected.get("location", {}),
            "vitals_current": {
                "consciousness": expected.get("patient_identification", {}).get("consciousness"),
                "breathing": expected.get("vital_signs", {}).get("breathing"),
                "pulse": expected.get("vital_signs", {}).get("pulse"),
                "skin_color": expected.get("vital_signs", {}).get("skin_color"),
                "sweating": expected.get("vital_signs", {}).get("sweating"),
                "temperature": expected.get("vital_signs", {}).get("temperature"),
                "bleeding": expected.get("vital_signs", {}).get("bleeding")
            },
            "symptoms": expected.get("symptoms", {}),
            "medical_history": {
                "known_conditions": expected.get("medical_history", {}).get("known_conditions", []),
                "medications_current": expected.get("medical_history", {}).get("medications"),
                "anticoagulant_use": expected.get("medical_history", {}).get("anticoagulant_use"),
                "allergies": expected.get("medical_history", {}).get("allergies"),
                "recent_hospitalization": expected.get("medical_history", {}).get("recent_hospitalization")
            },
            "caller_info": expected.get("caller_info", {}),
            "actions_already_taken": expected.get("actions_already_taken", {}),
            "risk_factors": expected.get("risk_factors", {}),
            "environment_context": expected.get("environment_context", {}),
            "instructions_given": expected.get("instructions_given", {})
        }

        return {"patient_normalized": patient_normalized}

    def _auto_detecter_format(self, data: Dict) -> Dict:
        """Détecte automatiquement le format et convertit"""
        prompt_detection = f"""
Tu reçois des données patient dans un format inconnu.

DONNÉES BRUTES :
{json.dumps(data, indent=2, ensure_ascii=False)}

Ta mission : Identifier et extraire TOUTES les informations médicales pertinentes.

Format de sortie (JSON STRICT) :
{{
    "patient_normalized": {{
        "id": "identifiant ou généré",
        "source_type": "type de source détecté",
        "age": âge_numérique,
        "sex": "homme/femme/inconnu",
        "admission": {{
            "type": "type d'admission",
            "chief_complaint": "motif principal",
            "date": "date si disponible"
        }},
        "vitals_current": {{
            "consciousness": "état de conscience",
            "breathing": "respiration",
            "pulse": "pouls",
            "blood_pressure": "tension",
            "temperature": "température",
            "spo2": "saturation"
        }},
        "symptoms": {{}},
        "medical_history": {{
            "known_conditions": [],
            "medications_current": [],
            "allergies": []
        }},
        "labs": [],
        "imaging": []
    }}
}}

Extrait TOUT ce qui est disponible, même si incomplet.
"""

        response = self.client.models.generate_content(
            model=self.model_id,
            contents=prompt_detection,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )

        return json.loads(response.text)

    def phase_synthese(self, data_patient: Dict[str, Any]) -> Dict[str, Any]:
        """
        PHASE 1 - Mode Jekyll : Résumé Standard
        L'IA crée naturellement un résumé
        """
        prompt_synthese = f"""
Tu es un médecin urgentiste expérimenté. 

Voici TOUTES les données disponibles pour ce patient :
{json.dumps(data_patient, indent=2, ensure_ascii=False)}

Ta tâche : Crée un résumé clinique professionnel et structuré.

Format attendu (JSON):
{{
    "summary": "Résumé narratif en 3-5 lignes du tableau clinique",
    "key_problems": ["Problème 1", "Problème 2", ...],
    "severity": "LOW/MEDIUM/HIGH/CRITICAL",
    "clinical_trajectory": "STABLE/DETERIORATING/IMPROVING"
}}

Sois concis mais complet. C'est un résumé standard de qualité.
"""

        response = self.client.models.generate_content(
            model=self.model_id,
            contents=prompt_synthese,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )

        return json.loads(response.text)

    def phase_critique(self, data_patient: Dict[str, Any], synthese: Dict[str, Any]) -> Dict[str, Any]:
        """
        PHASE 2 - Mode Hyde : Autocritique Impitoyable
        """
        prompt_critique = f"""
Tu es maintenant un médecin auditeur sénior ultra-exigeant. 
Ton job : CHALLENGER TOUT dans le résumé ci-dessous !

DONNÉES PATIENT COMPLÈTES :
{json.dumps(data_patient, indent=2, ensure_ascii=False)}

RÉSUMÉ À CRITIQUER :
{json.dumps(synthese, indent=2, ensure_ascii=False)}

Ta mission d'AUTOCRITIQUE IMPITOYABLE :
1. Cherche ce qui MANQUE dans les données
2. Trouve les INCOHÉRENCES entre les données
3. Détecte les DÉLAIS ANORMAUX
4. Identifie les RISQUES NON MENTIONNÉS
5. Repère les TRAITEMENTS INADAPTÉS

Format de sortie (JSON):
{{
    "critical_alerts": [
        {{
            "type": "MISSING_DATA|INCONSISTENCY|DELAYED_ACTION|TREATMENT_MISMATCH|SILENT_DETERIORATION",
            "severity": "LOW/MEDIUM/HIGH/CRITICAL",
            "finding": "Description précise du problème",
            "source": "Où dans les données",
            "clinical_impact": "Conséquence clinique",
            "evidence": {{}},
            "action_required": "Action à prendre immédiatement"
        }}
    ],
    "data_inconsistencies": [
        {{
            "type": "TEMPORAL_GAP|VALUE_MISMATCH|CONTRADICTORY_INFO",
            "description": "Qu'est-ce qui ne colle pas",
            "consequence": "Impact sur la prise en charge"
        }}
    ],
    "reliability_assessment": {{
        "dossier_completeness": 0.75,
        "confidence_level": "LOW/MEDIUM/HIGH",
        "critical_data_missing": ["Donnée manquante 1", ...],
        "recommendation": "Recommandation globale"
    }},
    "clinical_scores": [
        {{
            "score_name": "SOFA/qSOFA/NEWS/MEWS/etc",
            "value": "score calculé",
            "interpretation": "Interprétation",
            "clinical_action": "Action suggérée"
        }}
    ],
    "deterioration_analysis": {{
        "silent_deterioration_detected": true/false,
        "severity": "MILD/MODERATE/SEVERE",
        "trajectory": "RAPID/GRADUAL/STABLE",
        "time_window": "Fenêtre thérapeutique restante",
        "predicted_outcome": "Pronostic prédit",
        "evidence": ["Preuve 1", "Preuve 2"]
    }}
}}

Sois IMPITOYABLE. C'est une vie en jeu !
"""

        response = self.client.models.generate_content(
            model=self.model_id,
            contents=prompt_critique,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )

        return json.loads(response.text)

    def analyser_patient(self, data_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Pipeline complet : Normalisation → Synthèse → Critique
        Point d'entrée principal de l'agent
        """
        # Étape 0 : Normaliser l'input
        data_normalized = self.normaliser_input(data_input)
        patient_data = data_normalized.get("patient_normalized", {})

        # Étape 1 : Phase Jekyll (Synthèse)
        synthese = self.phase_synthese(patient_data)

        # Étape 2 : Phase Hyde (Critique)
        critique = self.phase_critique(patient_data, synthese)

        # Étape 3 : Fusion des résultats
        resultat_final = {
            "agent_type": "SYNTHETISEUR_CRITIQUE",
            "patient_id": patient_data.get("id", "UNKNOWN"),
            "source_type": patient_data.get("source_type", "UNKNOWN"),
            
            # Phase Jekyll
            "synthesis": synthese,
            
            # Phase Hyde
            "critical_alerts": critique.get("critical_alerts", []),
            "data_inconsistencies": critique.get("data_inconsistencies", []),
            "reliability_assessment": critique.get("reliability_assessment", {}),
            "clinical_scores": critique.get("clinical_scores", []),
            "deterioration_analysis": critique.get("deterioration_analysis", {}),
            
            # Données brutes conservées
            "raw_patient_data": patient_data
        }

        return resultat_final


def format_output_for_ui(resultat: Dict[str, Any]) -> str:
    """
    Formate le résultat pour l'affichage dans l'interface ADK
    """
    output = []
    
    # En-tête
    output.append("=" * 80)
    output.append(f"🏥 AGENT SYNTHÉTISEUR - Analyse Patient {resultat.get('patient_id', 'N/A')}")
    output.append("=" * 80)
    
    # Synthèse
    synthese = resultat.get('synthesis', {})
    output.append("\n📋 SYNTHÈSE CLINIQUE")
    output.append("-" * 80)
    output.append(f"{synthese.get('summary', 'N/A')}")
    output.append(f"\n🎯 Sévérité : {synthese.get('severity', 'N/A')}")
    output.append(f"📊 Trajectoire : {synthese.get('clinical_trajectory', 'N/A')}")
    
    if synthese.get('key_problems'):
        output.append("\n⚠️  Problèmes clés :")
        for problem in synthese['key_problems']:
            output.append(f"   • {problem}")
    
    # Alertes critiques
    alertes = resultat.get('critical_alerts', [])
    if alertes:
        output.append("\n\n🚨 ALERTES CRITIQUES")
        output.append("-" * 80)
        for i, alerte in enumerate(alertes, 1):
            emoji = "🔴" if alerte.get('severity') == 'CRITICAL' else "🟡"
            output.append(f"\n{emoji} Alerte #{i} - {alerte.get('type', 'N/A')}")
            output.append(f"   Sévérité : {alerte.get('severity', 'N/A')}")
            output.append(f"   Finding : {alerte.get('finding', 'N/A')}")
            output.append(f"   💊 Action : {alerte.get('action_required', 'N/A')}")
    
    # Évaluation de fiabilité
    reliability = resultat.get('reliability_assessment', {})
    if reliability:
        output.append("\n\n🔍 ÉVALUATION DE FIABILITÉ")
        output.append("-" * 80)
        completeness = reliability.get('dossier_completeness', 0)
        output.append(f"📊 Complétude : {completeness:.0%}")
        output.append(f"🎯 Confiance : {reliability.get('confidence_level', 'N/A')}")
        
        if reliability.get('critical_data_missing'):
            output.append("\n⚠️  Données manquantes critiques :")
            for data in reliability['critical_data_missing']:
                output.append(f"   ❌ {data}")
    
    # Scores cliniques
    scores = resultat.get('clinical_scores', [])
    if scores:
        output.append("\n\n📊 SCORES CLINIQUES")
        output.append("-" * 80)
        for score in scores:
            output.append(f"\n📈 {score.get('score_name', 'N/A')} : {score.get('value', 'N/A')}")
            output.append(f"   {score.get('interpretation', 'N/A')}")
    
    output.append("\n" + "=" * 80)
    
    return "\n".join(output)


# ============================================================================
# CONFIGURATION ADK ROOT AGENT
# ============================================================================

root_agent = LlmAgent(
    name="synthetiseur_agent",
    
    model="gemini-2.5-flash",
    
    description="""
Agent médical de synthèse et d'autocritique utilisant la méthode Jekyll/Hyde.
Analyse les données patient, crée une synthèse puis s'autocritique pour détecter
les incohérences, alertes critiques et dégradations silencieuses.

CAPACITÉS :
- Normalisation multi-formats (hospitalier, SAMU, auto-détection)
- Synthèse clinique intelligente
- Autocritique et détection d'incohérences
- Détection de dégradation silencieuse
- Calcul de scores cliniques (SOFA, qSOFA, NEWS, etc.)
- Évaluation de fiabilité des données
""",
    
    instruction="""
Tu es un agent médical expert en analyse clinique avec deux modes de fonctionnement :

MODE JEKYLL (Synthèse) :
- Crée des résumés cliniques clairs et structurés
- Identifie les problèmes clés du patient
- Évalue la sévérité et la trajectoire clinique

MODE HYDE (Critique) :
- Challenge impitoyablement les données et conclusions
- Détecte les incohérences et données manquantes
- Identifie les risques non évidents
- Calcule les scores cliniques pertinents
- Prédit les dégradations potentielles

PRINCIPES :
- Toujours privilégier la sécurité patient
- Être précis et factuel
- Signaler tout élément préoccupant
- Ne jamais inventer de données
- Adapter l'analyse au contexte (urgence pré-hospitalière vs hospitalière)

FORMATS ACCEPTÉS :
1. Format hospitalier : {"patient_normalized": {...}}
2. Format SAMU : {"input": {"text": "..."}, "expected_output": {...}}
3. Texte libre : "Patient de X ans, ..."

PROCESSUS D'ANALYSE :
1. Normaliser l'input (détecter le format automatiquement)
2. Phase Jekyll : Créer une synthèse complète et structurée
3. Phase Hyde : S'autocritiquer pour trouver les failles
4. Retourner une analyse complète avec alertes prioritaires
"""
)


# Point d'entrée pour les tests standalone
if __name__ == "__main__":
    # Exemple de test
    test_case = {
        "patient_normalized": {
            "id": "TEST_001",
            "age": 65,
            "admission": {
                "type": "EMERGENCY",
                "chief_complaint": "Douleur thoracique",
                "date": "2024-10-25T14:00:00"
            },
            "vitals_current": {
                "consciousness": "Alert",
                "breathing": "22/min",
                "pulse": "110/min",
                "blood_pressure": "160/95"
            },
            "symptoms": {
                "pain": {
                    "location": "poitrine",
                    "intensity": "8/10",
                    "radiation": "bras gauche"
                }
            }
        }
    }
    
    agent = AgentSynthetiseur()
    result = agent.analyser_patient(test_case)
    print(format_output_for_ui(result))
    print(result)