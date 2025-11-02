"""
Agent 2 : Synthétiseur/Critique - ADN (AI Diagnostic Navigator)
'Le Double Cerveau' - Résume puis s'auto-critique pour trouver les incohérences
Version GÉNÉRALISABLE - Pas de règles hardcodées
COMPATIBLE avec format hospitalier ET appels SAMU
"""

import json
from typing import Dict, List, Any
from google.cloud import aiplatform
from vertexai.generative_models import GenerativeModel


class AgentSynthetiseur:
    """
    Agent qui synthétise les données patient et s'autocritique
    SANS règles hardcodées - utilise uniquement l'IA pour généraliser
    COMPATIBLE avec format hospitalier ET appels SAMU
    """

    def __init__(self, project_id: str, location: str = "us-central1"):
        self.project_id = project_id
        self.location = location
        aiplatform.init(project=project_id, location=location)
        self.model = GenerativeModel("gemini-2.0-flash")

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
        """
        Convertit le format SAMU en format unifié
        """
        expected = data_samu.get("expected_output", {})
        meta = data_samu.get("meta", {})
        appel_text = data_samu.get("input", {}).get("text", "")

        # Construction du format normalisé
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
        """
        Détecte automatiquement le format et convertit
        Utilise l'IA pour identifier la structure
        """

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
        "symptoms": {{
            "pain": {{}},
            "neurological": {{}},
            "respiratory": {{}},
            "cardiac": {{}},
            "autres": {{}}
        }},
        "medical_history": {{
            "known_conditions": [],
            "medications_current": [],
            "allergies": []
        }},
        "labs": [],
        "imaging": [],
        "autres_donnees": {{}}
    }}
}}

Extrait TOUT ce qui est disponible, même si incomplet.
"""

        response = self.model.generate_content(
            prompt_detection,
            generation_config={"response_mime_type": "application/json"}
        )

        return json.loads(response.text)

    def phase_synthese(self, data_patient: Dict[str, Any]) -> Dict[str, Any]:
        """
        PHASE 1 - Mode Jekyll : Résumé Standard
        L'IA crée naturellement un résumé - AUCUNE règle explicite
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

        response = self.model.generate_content(
            prompt_synthese,
            generation_config={"response_mime_type": "application/json"}
        )

        synthese = json.loads(response.text)
        return synthese

    def phase_critique(self, synthese: Dict[str, Any], data_brutes: Dict[str, Any]) -> Dict[str, Any]:
        """
        PHASE 2 - Mode Hyde : Scepticisme Actif
        L'IA compare et détecte ELLE-MÊME les incohérences - AUCUNE règle
        """

        prompt_critique = f"""
🔴 CHANGEMENT DE RÔLE CRITIQUE 🔴

Tu es maintenant un médecin HYPER-SCEPTIQUE et paranoïaque sur la sécurité du patient.
Tu assumes que des erreurs fatales peuvent se cacher dans les données.

VOICI LE RÉSUMÉ qui vient d'être fait :
{json.dumps(synthese, indent=2, ensure_ascii=False)}

VOICI TOUTES LES DONNÉES BRUTES ORIGINALES :
{json.dumps(data_brutes, indent=2, ensure_ascii=False)}

TA MISSION CRITIQUE :
1. Compare ligne par ligne le résumé vs les données brutes
2. Trouve TOUT ce qui est manquant, minimisé, ou incohérent
3. Identifie les "signaux cachés" dangereux (résultats anormaux pas mentionnés, traitements manquants, délais suspects)
4. Détecte les contradictions temporelles (ex: résultat positif depuis 12h mais traitement non adapté)
5. Repère les antécédents enfouis dans les notes qui changent le diagnostic

Questions à te poser :
- Y a-t-il un résultat de labo/culture CRITIQUE qui n'est pas dans le résumé ?
- Y a-t-il un médicament qui devrait être là mais qui manque ?
- Y a-t-il un délai temporel suspect entre un résultat et une action ?
- Y a-t-il des antécédents cachés dans les notes textuelles qui sont ignorés ?
- Y a-t-il une dégradation clinique silencieuse (tendance des signes vitaux) ?

Format de sortie (JSON STRICT) :
{{
    "critical_alerts": [
        {{
            "type": "Type d'alerte (ex: RESULTAT_NON_TRAITE, INTERVENTION_MANQUANTE, etc.)",
            "severity": "HIGH/CRITICAL",
            "finding": "Description précise de ce qui manque ou est incohérent",
            "source": "Où dans data_brutes cette info se trouve",
            "clinical_impact": "Conséquence clinique potentielle",
            "evidence": {{
                "found_in": "Chemin exact dans les données",
                "value": "Valeur problématique",
                "comparison": "Ce qui était dans le résumé (ou absent)"
            }},
            "action_required": "Action médicale urgente nécessaire"
        }}
    ],
    "data_inconsistencies": [
        {{
            "type": "TEMPORAL_MISMATCH / MISSING_DATA / CONTRADICTION",
            "description": "Description de l'incohérence",
            "gap_hours": "Délai si applicable",
            "consequence": "Impact clinique"
        }}
    ],
    "reliability_assessment": {{
        "dossier_completeness": 0.0-1.0,
        "critical_data_missing": ["Liste des données critiques absentes"],
        "confidence_level": "LOW/MEDIUM/HIGH",
        "recommendation": "Recommandation sur la fiabilité de l'analyse"
    }}
}}

Sois IMPITOYABLE. Un patient peut mourir si tu rates quelque chose.
"""

        response = self.model.generate_content(
            prompt_critique,
            generation_config={"response_mime_type": "application/json"}
        )

        critique = json.loads(response.text)
        return critique

    def calculer_scores_cliniques(self, data_patient: Dict) -> Dict:
        """
        Calcule les scores cliniques standards (SOFA, qSOFA, etc.)
        Utilise l'IA pour identifier QUELS scores sont pertinents
        """

        prompt_scores = f"""
Tu es un expert en scores cliniques de médecine d'urgence.

Données patient :
{json.dumps(data_patient, indent=2, ensure_ascii=False)}

Identifie quels scores cliniques sont pertinents pour ce patient, puis calcule-les.
Exemples : SOFA, qSOFA, SIRS, CHA2DS2-VASc, CURB-65, etc.

Format JSON :
{{
    "applicable_scores": [
        {{
            "score_name": "Nom du score",
            "value": valeur_numérique,
            "interpretation": "Interprétation clinique",
            "components": {{"composante": valeur}},
            "clinical_action": "Action suggérée selon ce score"
        }}
    ]
}}
"""

        response = self.model.generate_content(
            prompt_scores,
            generation_config={"response_mime_type": "application/json"}
        )

        scores = json.loads(response.text)
        return scores

    def detecter_degradation_silencieuse(self, data_patient: Dict) -> Dict:
        """
        Détecte les tendances inquiétantes dans les signes vitaux
        L'IA analyse les patterns temporels ELLE-MÊME
        """

        prompt_tendance = f"""
Analyse les tendances cliniques pour détecter une dégradation silencieuse.

Données patient avec historique temporel :
{json.dumps(data_patient, indent=2, ensure_ascii=False)}

Cherche :
- Tendances des signes vitaux (FC qui monte, TA qui baisse, etc.)
- Aggravation progressive des labs (lactate qui monte, créat qui monte)
- Pattern de dégradation multi-organique
- Signes précoces de choc ou défaillance d'organe

Format JSON :
{{
    "silent_deterioration_detected": true/false,
    "severity": "LOW/MEDIUM/HIGH",
    "trajectory": "STABLE/SLOW_DETERIORATION/RAPID_DETERIORATION",
    "evidence": ["Signal 1", "Signal 2", ...],
    "predicted_outcome": "Pronostic probable si non traité",
    "time_window": "Fenêtre thérapeutique estimée"
}}
"""

        response = self.model.generate_content(
            prompt_tendance,
            generation_config={"response_mime_type": "application/json"}
        )

        deterioration = json.loads(response.text)
        return deterioration

    def analyser_patient(self, data_input: Dict) -> Dict:
        """
        Pipeline complet : Normalisation + Synthèse + Critique + Validation
        100% générique - s'adapte à N'IMPORTE QUEL format et pathologie
        """
        # ÉTAPE 0 : Normalisation de l'input
        print("🔄 Étape 0 : Normalisation du format d'entrée...")
        data_collecteur = self.normaliser_input(data_input)
        print("✅ Format normalisé")

        print("\n🔄 Phase 1 : Synthèse Jekyll (Mode Bienveillant)...")
        synthese = self.phase_synthese(data_collecteur)
        print(f"✅ Synthèse créée")
        print(f"   Problèmes identifiés : {', '.join(synthese.get('key_problems', []))}")
        print(f"   Sévérité : {synthese.get('severity', 'N/A')}")

        print("\n⚠️ Phase 2 : Critique Hyde (Mode Sceptique)...")
        critique = self.phase_critique(synthese, data_collecteur)
        nb_alertes = len(critique.get('critical_alerts', []))
        print(f"🔍 {nb_alertes} alertes critiques détectées")

        print("\n📊 Phase 3 : Calcul des scores cliniques...")
        scores = self.calculer_scores_cliniques(data_collecteur)
        print(f"   Scores calculés : {', '.join([s['score_name'] for s in scores.get('applicable_scores', [])])}")

        print("\n📈 Phase 4 : Détection de dégradation silencieuse...")
        deterioration = self.detecter_degradation_silencieuse(data_collecteur)
        print(f"   Trajectoire : {deterioration.get('trajectory', 'N/A')}")

        # Résultat final combiné
        output = {
            "source_data": data_collecteur,  # Inclut les données normalisées
            "synthesis": synthese,
            "critical_alerts": critique.get("critical_alerts", []),
            "data_inconsistencies": critique.get("data_inconsistencies", []),
            "reliability_assessment": critique.get("reliability_assessment", {}),
            "clinical_scores": scores.get("applicable_scores", []),
            "deterioration_analysis": deterioration
        }

        return output


# Fonction d'affichage détaillé
def afficher_resultats_detailles(resultat: Dict, titre_cas: str):
    """
    Affiche les résultats de manière détaillée comme dans les slides
    """
    print("\n" + "=" * 100)
    print(f"📋 RÉSULTATS DÉTAILLÉS - {titre_cas}")
    print("=" * 100)

    # 1. SYNTHÈSE
    print("\n┌─────────────────────────────────────────────────────────────┐")
    print("│  📝 SYNTHÈSE CLINIQUE (Phase Jekyll)                        │")
    print("└─────────────────────────────────────────────────────────────┘")
    synthese = resultat['synthesis']
    print(f"\n{synthese.get('summary', 'N/A')}\n")
    print(f"🎯 Problèmes clés : {', '.join(synthese.get('key_problems', []))}")
    print(f"⚠️  Sévérité : {synthese.get('severity', 'N/A')}")
    print(f"📈 Trajectoire : {synthese.get('clinical_trajectory', 'N/A')}")

    # 2. ALERTES CRITIQUES
    alertes = resultat.get('critical_alerts', [])
    print("\n┌─────────────────────────────────────────────────────────────┐")
    print(f"│  🚨 ALERTES CRITIQUES (Phase Hyde) - {len(alertes)} détectée(s)    │")
    print("└─────────────────────────────────────────────────────────────┘")

    if alertes:
        for i, alerte in enumerate(alertes, 1):
            severite_emoji = "🔴" if alerte.get('severity') == 'CRITICAL' else "🟡"
            print(f"\n{severite_emoji} ALERTE #{i} - {alerte.get('type', 'N/A')}")
            print(f"   Sévérité : {alerte.get('severity', 'N/A')}")
            print(f"   Finding : {alerte.get('finding', 'N/A')}")
            print(f"   Source : {alerte.get('source', 'N/A')}")
            print(f"   Impact clinique : {alerte.get('clinical_impact', 'N/A')}")

            if 'evidence' in alerte:
                print(f"   📊 Evidence :")
                for key, value in alerte['evidence'].items():
                    print(f"      - {key}: {value}")

            print(f"   💊 Action requise : {alerte.get('action_required', 'N/A')}")
    else:
        print("\n✅ Aucune alerte critique détectée")

    # 3. INCOHÉRENCES DE DONNÉES
    inconsistencies = resultat.get('data_inconsistencies', [])
    if inconsistencies:
        print("\n┌─────────────────────────────────────────────────────────────┐")
        print(f"│  ⚠️  INCOHÉRENCES DÉTECTÉES - {len(inconsistencies)} trouvée(s)        │")
        print("└─────────────────────────────────────────────────────────────┘")

        for i, inco in enumerate(inconsistencies, 1):
            print(f"\n⚠️  Incohérence #{i} - {inco.get('type', 'N/A')}")
            print(f"   Description : {inco.get('description', 'N/A')}")
            if 'gap_hours' in inco:
                print(f"   Délai : {inco.get('gap_hours')} heures")
            print(f"   Conséquence : {inco.get('consequence', 'N/A')}")

    # 4. ÉVALUATION DE FIABILITÉ (AUTOCRITIQUE)
    reliability = resultat.get('reliability_assessment', {})
    print("\n┌─────────────────────────────────────────────────────────────┐")
    print("│  🔍 ÉVALUATION DE FIABILITÉ (Autocritique)                  │")
    print("└─────────────────────────────────────────────────────────────┘")

    completeness = reliability.get('dossier_completeness', 0)
    print(f"\n📊 Complétude du dossier : {completeness:.0%}")
    print(f"🎯 Niveau de confiance : {reliability.get('confidence_level', 'N/A')}")

    missing = reliability.get('critical_data_missing', [])
    if missing:
        print(f"\n⚠️  Données critiques manquantes :")
        for data in missing:
            print(f"   ❌ {data}")

    print(f"\n💡 Recommandation : {reliability.get('recommendation', 'N/A')}")

    # 5. SCORES CLINIQUES
    scores = resultat.get('clinical_scores', [])
    if scores:
        print("\n┌─────────────────────────────────────────────────────────────┐")
        print(f"│  📊 SCORES CLINIQUES - {len(scores)} calculé(s)                    │")
        print("└─────────────────────────────────────────────────────────────┘")

        for score in scores:
            print(f"\n📈 {score.get('score_name', 'N/A')} : {score.get('value', 'N/A')}")
            print(f"   Interprétation : {score.get('interpretation', 'N/A')}")
            if 'components' in score:
                print(f"   Composantes : {score['components']}")
            print(f"   Action suggérée : {score.get('clinical_action', 'N/A')}")

    # 6. ANALYSE DE DÉGRADATION
    deterioration = resultat.get('deterioration_analysis', {})
    if deterioration.get('silent_deterioration_detected'):
        print("\n┌─────────────────────────────────────────────────────────────┐")
        print("│  📉 DÉGRADATION SILENCIEUSE DÉTECTÉE                        │")
        print("└─────────────────────────────────────────────────────────────┘")

        print(f"\n⚠️  Sévérité : {deterioration.get('severity', 'N/A')}")
        print(f"📈 Trajectoire : {deterioration.get('trajectory', 'N/A')}")
        print(f"⏰ Fenêtre thérapeutique : {deterioration.get('time_window', 'N/A')}")
        print(f"🔮 Pronostic prédit : {deterioration.get('predicted_outcome', 'N/A')}")

        evidence = deterioration.get('evidence', [])
        if evidence:
            print(f"\n📊 Preuves de dégradation :")
            for ev in evidence:
                print(f"   • {ev}")

    # 7. JSON COMPLET (comme dans les slides)
    print("\n┌─────────────────────────────────────────────────────────────┐")
    print("│  📄 OUTPUT JSON COMPLET (Format Agent)                      │")
    print("└─────────────────────────────────────────────────────────────┘")
    print("\n```json")
    print(json.dumps(resultat, indent=2, ensure_ascii=False))
    print("```")

    print("\n" + "=" * 100 + "\n")


# Exemple d'utilisation avec N'IMPORTE QUEL format
if __name__ == "__main__":
    # FORMAT 1 : Cas hospitalier (format original)
    cas_sepsis = {
        "patient_normalized": {
            "id": "10006",
            "age": 70,
            "admission": {
                "type": "EMERGENCY",
                "chief_complaint": "SEPSIS",
                "date": "2024-10-14T14:15:00"
            },
            "labs": [
                {"name": "WBC", "value": 18000, "unit": "cells/μL", "flag": "HIGH"},
                {"name": "Lactate", "value": 3.2, "unit": "mmol/L", "flag": "HIGH"}
            ],
            "cultures": [
                {
                    "status": "POSITIVE",
                    "organism": "Staphylococcus aureus (MRSA)",
                    "collected": "2024-10-14T02:30:00",
                    "resulted": "2024-10-14T14:30:00",
                    "antibiogram": {"oxacillin": "R", "vancomycin": "S"}
                }
            ],
            "medications_current": [
                {"name": "Ceftriaxone", "dose": "2g", "route": "IV"}
            ]
        }
    }

    # FORMAT 2 : Appel SAMU - Douleur thoracique (TON FORMAT)
    cas_samu_infarctus = {
        "id": "cardiac_case_01",
        "meta": {
            "scenario": "douleur thoracique / malaise à domicile",
            "difficulty": "moyen",
            "source": "synthetic",
            "language": "fr"
        },
        "input": {
            "text": "Bonjour, je vous appelle pour mon mari. Il a 58 ans, il est tombé dans le salon il y a environ 10 minutes. Il est conscient mais très pâle et se plaint d'une forte douleur à la poitrine. Il transpire beaucoup et dit qu'il a mal au bras gauche."
        },
        "expected_output": {
            "caller_info": {
                "relationship_to_patient": "épouse"
            },
            "location": {
                "address": "24 rue de la République, 3e étage sans ascenseur",
                "city": "Lyon"
            },
            "incident_description": {
                "main_reason": "douleur thoracique après malaise",
                "mechanism": "effondrement soudain non traumatique",
                "onset_time": "il y a environ 10 minutes"
            },
            "patient_identification": {
                "age": 58,
                "sex": "homme",
                "consciousness": "conscient"
            },
            "vital_signs": {
                "breathing": "rapide mais présente",
                "skin_color": "pâle",
                "sweating": "oui"
            },
            "symptoms": {
                "pain": {
                    "location": "poitrine",
                    "intensity": "sévère",
                    "radiation": "bras gauche"
                }
            },
            "medical_history": {
                "known_conditions": ["hypertension", "maladie cardiaque"],
                "medications": "bêta-bloquant pour le cœur"
            }
        }
    }

    # L'agent fonctionne sur TOUS ces formats différents !
    agent2 = AgentSynthetiseur(project_id="ai-diagnostic-navigator-475316")

    print("=" * 80)
    print("TEST 1 : Sepsis SARM (Format Hospitalier)")
    print("=" * 80)
    resultat1 = agent2.analyser_patient(cas_sepsis)

    print("\n\n" + "=" * 80)
    print("TEST 2 : Infarctus (Format SAMU)")
    print("=" * 80)
    resultat2 = agent2.analyser_patient(cas_samu_infarctus)
    # print(resultat2)

    # Affichage détaillé
    # afficher_resultats_detailles(resultat1, "Sepsis SARM - Hospitalier")
    # afficher_resultats_detailles(resultat2, "Infarctus - Appel SAMU")

    print("\n\n" + "=" * 80)
    print("TEST 3 : Output Agent récolteur")
    print("=" * 80)
    # resultat2 = agent2.analyser_patient("??????????")