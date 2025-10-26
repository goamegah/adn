"""
Agent 3 Expert ADK - ADN (AI Diagnostic Navigator)
'Le Professeur de Médecine' - Valide avec guidelines et génère diagnostics différentiels
Compatible avec l'architecture ADK
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from google import genai
from google.genai import types
from google.adk.agents import LlmAgent

from dotenv import load_dotenv
ENV_PATH = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=ENV_PATH, override=True)


class AgentExpert:
    """
    Agent 3 : Expert qui valide les alertes avec des guidelines médicales
    et génère des diagnostics différentiels
    Compatible avec l'interface ADK
    """

    def __init__(self):
        """Initialise l'agent avec le client Gemini"""
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.client = genai.Client(api_key=self.api_key)
        self.model_id = "gemini-2.0-flash-exp"
        
        # Configuration RAG (Vertex AI Search - optionnel si disponible)
        self.rag_disponible = False
        self.datastore_id = None

    def phase_diagnostics_differentiels(
        self, 
        output_agent2: Dict[str, Any]
    ) -> List[Dict]:
        """
        PHASE 1 : Génération des diagnostics différentiels
        """
        synthese = output_agent2.get("synthesis", {})
        alertes = output_agent2.get("critical_alerts", [])
        data_patient = output_agent2.get("raw_patient_data", {})
        scores = output_agent2.get("clinical_scores", [])
        
        contexte_clinique = self._construire_contexte_clinique(
            synthese, alertes, data_patient, scores
        )
        
        prompt_diagnostics = f"""
Tu es un expert en médecine d'urgence et infectiologie.

CONTEXTE CLINIQUE COMPLET :
{json.dumps(contexte_clinique, indent=2, ensure_ascii=False)}

Ta mission : Générer une liste de diagnostics différentiels pertinents.

Pour chaque diagnostic, fournis :
1. Le nom du diagnostic
2. La probabilité (HIGH/MEDIUM/LOW)
3. Un score de confiance (0.0 à 1.0)
4. Les critères qui soutiennent ce diagnostic (trouvés dans les données)
5. Les critères qui vont contre ce diagnostic
6. Les examens complémentaires nécessaires pour confirmer/infirmer

Format JSON strict :
{{
    "differential_diagnoses": [
        {{
            "diagnosis": "Nom du diagnostic",
            "icd10_code": "Code ICD-10 si applicable",
            "probability": "HIGH/MEDIUM/LOW",
            "confidence_score": 0.85,
            "supporting_evidence": [
                {{
                    "finding": "Élément clinique",
                    "strength": "DEFINITIVE/STRONG/MODERATE/WEAK",
                    "source": "D'où vient cette info"
                }}
            ],
            "contradicting_evidence": [
                {{
                    "finding": "Élément qui va contre",
                    "impact": "MAJOR/MODERATE/MINOR"
                }}
            ],
            "additional_tests_needed": [
                "Examen 1",
                "Examen 2"
            ],
            "urgency": "IMMEDIATE/URGENT/ROUTINE",
            "typical_presentation": "Description de la présentation typique",
            "atypical_features": ["Caractéristique atypique observée"]
        }}
    ]
}}

Classe les diagnostics par probabilité décroissante.
Sois exhaustif mais pertinent - inclus les diagnostics graves même si moins probables.
"""
        
        response = self.client.models.generate_content(
            model=self.model_id,
            contents=prompt_diagnostics,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        
        result = json.loads(response.text)
        return result.get("differential_diagnoses", [])

    def phase_validation_guidelines(
        self, 
        alertes: List[Dict], 
        data_patient: Dict
    ) -> List[Dict]:
        """
        PHASE 2 : Validation des alertes contre les guidelines médicales
        """
        alertes_validees = []
        
        for alerte in alertes:
            prompt_validation = f"""
Tu es un expert en médecine basée sur les preuves.

ALERTE À VALIDER :
{json.dumps(alerte, indent=2, ensure_ascii=False)}

CONTEXTE PATIENT :
{json.dumps(data_patient, indent=2, ensure_ascii=False)}

Ta mission : Valider cette alerte contre les guidelines médicales reconnues.

Format JSON :
{{
    "alert_validated": true/false,
    "validation_strength": "STRONG/MODERATE/WEAK",
    "guidelines_references": [
        {{
            "guideline_name": "Nom de la guideline (ex: Surviving Sepsis Campaign 2021)",
            "recommendation": "Recommandation exacte",
            "strength_of_evidence": "HIGH/MODERATE/LOW",
            "source_url": "URL si disponible",
            "quote": "Citation pertinente de la guideline"
        }}
    ],
    "clinical_evidence": [
        {{
            "evidence_type": "RCT/Meta-analysis/Observational/Expert opinion",
            "finding": "Résultat de l'étude",
            "relevance": "Description de la pertinence pour ce cas"
        }}
    ],
    "action_urgency_validated": "IMMEDIATE/WITHIN_1H/WITHIN_6H/ROUTINE",
    "alternative_approaches": [
        "Approche alternative 1 si la première n'est pas possible"
    ],
    "contraindications_check": {{
        "contraindications_present": false,
        "details": "Vérification des contre-indications"
    }}
}}
"""
            
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=prompt_validation,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            
            validation = json.loads(response.text)
            
            # Combiner l'alerte originale avec la validation
            alerte_validee = {
                **alerte,
                "validation": validation
            }
            
            alertes_validees.append(alerte_validee)
        
        return alertes_validees

    def phase_scores_risque(
        self, 
        diagnostics: List[Dict], 
        data_patient: Dict
    ) -> List[Dict]:
        """
        PHASE 3 : Calcul des scores de risque additionnels
        """
        prompt_scores = f"""
Tu es un expert en scores cliniques et pronostic.

DIAGNOSTICS RETENUS :
{json.dumps(diagnostics[:3], indent=2, ensure_ascii=False)}

DONNÉES PATIENT :
{json.dumps(data_patient, indent=2, ensure_ascii=False)}

Pour chaque diagnostic, calcule les scores de risque pertinents.

Exemples de scores selon le diagnostic :
- Sepsis : APACHE II, SAPS II, mortalité prédite
- Infarctus : GRACE, TIMI, risque de décès à 30j
- AVC : NIHSS, ASPECT, risque hémorragique si thrombolyse
- Embolie pulmonaire : score de Wells, PESI, sPESI

Format JSON :
{{
    "risk_scores": [
        {{
            "diagnosis_related": "Diagnostic concerné",
            "score_name": "Nom du score",
            "score_value": valeur_numérique,
            "interpretation": "Interprétation du score",
            "risk_category": "LOW/INTERMEDIATE/HIGH",
            "predicted_outcomes": {{
                "mortality_30d": "Pourcentage ou catégorie",
                "complications": ["Complication possible 1"],
                "icu_length_of_stay": "Estimation"
            }},
            "components_breakdown": {{"composante": "valeur"}},
            "confidence_in_calculation": "HIGH/MEDIUM/LOW avec justification"
        }}
    ]
}}
"""
        
        response = self.client.models.generate_content(
            model=self.model_id,
            contents=prompt_scores,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        
        result = json.loads(response.text)
        return result.get("risk_scores", [])

    def phase_plan_action(
        self,
        alertes_validees: List[Dict],
        diagnostics: List[Dict],
        data_patient: Dict
    ) -> Dict:
        """
        PHASE 4 : Génération du plan d'action concret et sourcé
        """
        prompt_action = f"""
Tu es un médecin urgentiste qui crée un plan d'action concret.

ALERTES VALIDÉES :
{json.dumps(alertes_validees, indent=2, ensure_ascii=False)}

DIAGNOSTICS DIFFÉRENTIELS :
{json.dumps(diagnostics[:3], indent=2, ensure_ascii=False)}

DONNÉES PATIENT :
{json.dumps(data_patient, indent=2, ensure_ascii=False)}

Crée un plan d'action structuré et priorisé.

Format JSON :
{{
    "immediate_actions": [
        {{
            "action": "Action à prendre MAINTENANT (< 15 min)",
            "justification": "Pourquoi c'est urgent",
            "guideline_reference": "Référence guideline",
            "expected_outcome": "Résultat attendu",
            "monitoring": "Comment surveiller l'effet"
        }}
    ],
    "urgent_actions": [
        {{
            "action": "Action dans l'heure",
            "timeframe": "< 1h",
            "justification": "Justification",
            "guideline_reference": "Référence"
        }}
    ],
    "diagnostic_workup": [
        {{
            "test": "Examen à réaliser",
            "indication": "Pourquoi",
            "priority": "HIGH/MEDIUM/LOW",
            "expected_turnaround": "Délai de résultat",
            "interpretation_guide": "Comment interpréter"
        }}
    ],
    "monitoring_plan": [
        {{
            "parameter": "Paramètre à surveiller",
            "frequency": "Fréquence de surveillance",
            "alert_threshold": "Seuil d'alerte",
            "escalation_if": "Quand escalader"
        }}
    ],
    "consultation_needs": [
        {{
            "specialty": "Spécialité à consulter",
            "urgency": "IMMEDIATE/URGENT/ROUTINE",
            "reason": "Raison de la consultation",
            "questions_to_address": ["Question 1"]
        }}
    ],
    "medication_adjustments": [
        {{
            "medication": "Médicament",
            "action": "START/STOP/ADJUST",
            "dosing": "Posologie recommandée",
            "monitoring_required": "Surveillance nécessaire",
            "guideline_reference": "Référence"
        }}
    ],
    "disposition": {{
        "recommended_location": "USI/USC/Étage/Domicile",
        "justification": "Justification de l'orientation",
        "criteria_for_discharge": ["Critère pour sortie si applicable"],
        "follow_up_plan": "Plan de suivi"
    }}
}}
"""
        
        response = self.client.models.generate_content(
            model=self.model_id,
            contents=prompt_action,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        
        return json.loads(response.text)

    def analyser_alertes(self, output_agent2: Dict[str, Any]) -> Dict[str, Any]:
        """
        Pipeline complet : Diagnostics → Validation → Scores → Action
        Point d'entrée principal de l'agent
        """
        print("🎓 Agent 3 Expert (ADK) : Démarrage de l'analyse...")
        
        # Extraction des données
        synthese = output_agent2.get("synthesis", {})
        alertes = output_agent2.get("critical_alerts", [])
        data_patient = output_agent2.get("raw_patient_data", {})
        scores = output_agent2.get("clinical_scores", [])
        
        # Phase 1 : Diagnostics différentiels
        print("\n📊 Phase 1 : Génération des diagnostics différentiels...")
        diagnostics = self.phase_diagnostics_differentiels(output_agent2)
        
        # Phase 2 : Validation des alertes
        print("\n📚 Phase 2 : Validation avec guidelines médicales...")
        alertes_validees = self.phase_validation_guidelines(alertes, data_patient)
        
        # Phase 3 : Scores de risque
        print("\n🎯 Phase 3 : Calcul des scores de risque...")
        scores_risque = self.phase_scores_risque(diagnostics, data_patient)
        
        # Phase 4 : Plan d'action
        print("\n💊 Phase 4 : Génération du plan d'action...")
        plan_action = self.phase_plan_action(alertes_validees, diagnostics, data_patient)
        
        # Phase 5 : Synthèse des preuves
        print("\n📖 Phase 5 : Synthèse des preuves...")
        synthese_preuves = self._generer_synthese_preuves(diagnostics, alertes_validees)
        
        # Résultat final
        resultat_final = {
            "agent_type": "EXPERT_VALIDATION",
            "patient_id": data_patient.get("id", "UNKNOWN"),
            "source_synthesis": synthese.get("summary", ""),
            
            # Résultats des phases
            "differential_diagnoses": diagnostics,
            "validated_alerts": alertes_validees,
            "risk_scores": scores_risque,
            "action_plan": plan_action,
            "evidence_summary": synthese_preuves,
            
            # Données source conservées
            "source_data": {
                "patient_normalized": data_patient,
                "original_synthesis": synthese,
                "original_alerts": alertes,
                "original_scores": scores
            }
        }
        
        print("\n✅ Agent 3 Expert (ADK) : Analyse terminée")
        
        return resultat_final

    def _construire_contexte_clinique(
        self,
        synthese: Dict,
        alertes: List[Dict],
        data_patient: Dict,
        scores: List[Dict]
    ) -> Dict:
        """
        Construit un contexte clinique structuré pour l'IA
        """
        return {
            "presentation_clinique": synthese.get("summary", ""),
            "problemes_principaux": synthese.get("key_problems", []),
            "severite": synthese.get("severity", ""),
            "trajectoire": synthese.get("clinical_trajectory", ""),
            "alertes_critiques": [
                {
                    "type": a.get("type"),
                    "finding": a.get("finding"),
                    "severity": a.get("severity")
                }
                for a in alertes
            ],
            "donnees_patient": {
                "age": data_patient.get("age"),
                "sex": data_patient.get("sex"),
                "antecedents": data_patient.get("medical_history", {}).get("known_conditions", []),
                "medicaments": data_patient.get("medications_current", []) or 
                              data_patient.get("medical_history", {}).get("medications_current", []),
                "signes_vitaux": data_patient.get("vitals_current", {}),
                "laboratoire": data_patient.get("labs", []),
                "microbiologie": data_patient.get("cultures", [])
            },
            "scores_cliniques": scores
        }

    def _generer_synthese_preuves(
        self,
        diagnostics: List[Dict],
        alertes_validees: List[Dict]
    ) -> Dict:
        """
        Génère une synthèse des preuves et références
        """
        # Extraire toutes les références
        toutes_references = []
        
        for alerte in alertes_validees:
            if "validation" in alerte:
                refs = alerte["validation"].get("guidelines_references", [])
                toutes_references.extend(refs)
        
        # Déduplication et tri
        references_uniques = []
        vues = set()
        for ref in toutes_references:
            nom = ref.get("guideline_name", "")
            if nom and nom not in vues:
                vues.add(nom)
                references_uniques.append(ref)
        
        return {
            "total_references": len(references_uniques),
            "guidelines_cited": references_uniques,
            "evidence_strength_summary": {
                "high_quality": len([r for r in references_uniques if r.get("strength_of_evidence") == "HIGH"]),
                "moderate_quality": len([r for r in references_uniques if r.get("strength_of_evidence") == "MODERATE"]),
                "low_quality": len([r for r in references_uniques if r.get("strength_of_evidence") == "LOW"])
            },
            "key_recommendations": [
                ref.get("recommendation")
                for ref in references_uniques[:5]
                if ref.get("recommendation")
            ]
        }


def format_output_for_ui(resultat: Dict[str, Any]) -> str:
    """
    Formate le résultat pour l'affichage dans l'interface ADK
    """
    output = []
    
    # En-tête
    output.append("=" * 100)
    output.append(f"🎓 AGENT EXPERT - Validation Médicale Patient {resultat.get('patient_id', 'N/A')}")
    output.append("=" * 100)
    
    # 1. DIAGNOSTICS DIFFÉRENTIELS
    diagnostics = resultat.get("differential_diagnoses", [])
    output.append(f"\n┌{'─'*98}┐")
    output.append(f"│  🔍 DIAGNOSTICS DIFFÉRENTIELS - {len(diagnostics)} identifié(s){' '*(98-len(f'  🔍 DIAGNOSTICS DIFFÉRENTIELS - {len(diagnostics)} identifié(s)'))}│")
    output.append(f"└{'─'*98}┘")
    
    for i, diag in enumerate(diagnostics, 1):
        prob_emoji = "🔴" if diag.get("probability") == "HIGH" else "🟡" if diag.get("probability") == "MEDIUM" else "🟢"
        output.append(f"\n{prob_emoji} DIAGNOSTIC #{i} - {diag.get('diagnosis', 'N/A')}")
        output.append(f"   Code ICD-10 : {diag.get('icd10_code', 'N/A')}")
        output.append(f"   Probabilité : {diag.get('probability', 'N/A')} | Confiance : {diag.get('confidence_score', 0):.2f}")
        output.append(f"   Urgence : {diag.get('urgency', 'N/A')}")
        
        evidence_for = diag.get("supporting_evidence", [])
        if evidence_for:
            output.append(f"\n   ✅ Arguments POUR ({len(evidence_for)}) :")
            for ev in evidence_for[:3]:
                output.append(f"      • {ev.get('finding')} (force: {ev.get('strength')})")
        
        evidence_against = diag.get("contradicting_evidence", [])
        if evidence_against:
            output.append(f"\n   ❌ Arguments CONTRE ({len(evidence_against)}) :")
            for ev in evidence_against[:2]:
                output.append(f"      • {ev.get('finding')} (impact: {ev.get('impact')})")
        
        tests = diag.get("additional_tests_needed", [])
        if tests:
            output.append(f"\n   🔬 Examens nécessaires : {', '.join(tests[:3])}")
    
    # 2. ALERTES VALIDÉES
    alertes_val = resultat.get("validated_alerts", [])
    output.append(f"\n\n┌{'─'*98}┐")
    output.append(f"│  ✅ ALERTES VALIDÉES - {len(alertes_val)} alerte(s){' '*(98-len(f'  ✅ ALERTES VALIDÉES - {len(alertes_val)} alerte(s)'))}│")
    output.append(f"└{'─'*98}┘")
    
    for alerte in alertes_val:
        validation = alerte.get("validation", {})
        validated = validation.get("alert_validated", False)
        strength = validation.get("validation_strength", "N/A")
        
        emoji = "✅" if validated else "⚠️"
        output.append(f"\n{emoji} {alerte.get('type', 'N/A')}")
        output.append(f"   Finding : {alerte.get('finding', 'N/A')}")
        output.append(f"   Validation : {validated} (force: {strength})")
        output.append(f"   Urgence : {validation.get('action_urgency_validated', 'N/A')}")
        
        guidelines = validation.get("guidelines_references", [])
        if guidelines:
            output.append(f"\n   📚 Guidelines ({len(guidelines)}) :")
            for guide in guidelines[:2]:
                output.append(f"      • {guide.get('guideline_name')}")
                rec = guide.get('recommendation', '')
                if rec:
                    output.append(f"        → {rec[:80]}...")
    
    # 3. PLAN D'ACTION
    plan = resultat.get("action_plan", {})
    output.append(f"\n\n┌{'─'*98}┐")
    output.append(f"│  💊 PLAN D'ACTION{' '*83}│")
    output.append(f"└{'─'*98}┘")
    
    immediate = plan.get("immediate_actions", [])
    if immediate:
        output.append(f"\n🚨 ACTIONS IMMÉDIATES (< 15 min) - {len(immediate)} action(s) :")
        for action in immediate:
            output.append(f"   • {action.get('action')}")
            output.append(f"     ↳ {action.get('justification')}")
    
    urgent = plan.get("urgent_actions", [])
    if urgent:
        output.append(f"\n⏰ ACTIONS URGENTES (< 1h) - {len(urgent)} action(s) :")
        for action in urgent:
            output.append(f"   • {action.get('action')} - {action.get('timeframe')}")
    
    monitoring = plan.get("monitoring_plan", [])
    if monitoring:
        output.append(f"\n📊 SURVEILLANCE - {len(monitoring)} paramètre(s) :")
        for item in monitoring[:3]:
            output.append(f"   • {item.get('parameter')} - {item.get('frequency')}")
    
    # 4. SCORES DE RISQUE
    scores = resultat.get("risk_scores", [])
    if scores:
        output.append(f"\n\n┌{'─'*98}┐")
        output.append(f"│  🎯 SCORES DE RISQUE - {len(scores)} score(s){' '*(98-len(f'  🎯 SCORES DE RISQUE - {len(scores)} score(s)'))}│")
        output.append(f"└{'─'*98}┘")
        
        for score in scores:
            output.append(f"\n📈 {score.get('score_name', 'N/A')} : {score.get('score_value', 'N/A')}")
            output.append(f"   Catégorie : {score.get('risk_category', 'N/A')}")
            output.append(f"   Interprétation : {score.get('interpretation', 'N/A')}")
    
    # 5. SYNTHÈSE DES PREUVES
    evidence = resultat.get("evidence_summary", {})
    output.append(f"\n\n┌{'─'*98}┐")
    output.append(f"│  📚 SYNTHÈSE DES PREUVES{' '*73}│")
    output.append(f"└{'─'*98}┘")
    
    output.append(f"\n📊 Total références : {evidence.get('total_references', 0)}")
    
    strength_summary = evidence.get("evidence_strength_summary", {})
    if strength_summary:
        output.append(f"\n🎯 Qualité des preuves :")
        output.append(f"   • Haute : {strength_summary.get('high_quality', 0)}")
        output.append(f"   • Moyenne : {strength_summary.get('moderate_quality', 0)}")
        output.append(f"   • Basse : {strength_summary.get('low_quality', 0)}")
    
    output.append("\n" + "=" * 100)
    
    return "\n".join(output)


# ============================================================================
# CONFIGURATION ADK ROOT AGENT
# ============================================================================

root_agent = LlmAgent(
    name="expert_agent",
    
    model="gemini-2.0-flash-exp",
    
    description="""
Agent médical expert en validation clinique et diagnostics différentiels.
Analyse les alertes de l'Agent Synthétiseur, valide contre les guidelines médicales,
génère des diagnostics différentiels et propose des plans d'action sourcés.

CAPACITÉS :
- Génération de diagnostics différentiels avec preuves
- Validation des alertes contre guidelines internationales
- Calcul de scores de risque spécialisés (APACHE II, GRACE, TIMI, NIHSS, etc.)
- Génération de plans d'action priorisés et sourcés
- Synthèse des preuves et références médicales
""",
    
    instruction="""
Tu es un professeur de médecine expert en médecine d'urgence et infectiologie.

RÔLE :
- Valider les alertes cliniques contre les guidelines médicales reconnues
- Générer des diagnostics différentiels basés sur les preuves
- Calculer des scores de risque pertinents
- Proposer des plans d'action sourcés et priorisés

PROCESSUS EN 5 PHASES :

PHASE 1 - DIAGNOSTICS DIFFÉRENTIELS :
- Génère une liste complète et pertinente de diagnostics
- Pour chaque diagnostic : probabilité, confiance, preuves POUR/CONTRE
- Inclut les diagnostics graves même si moins probables
- Identifie les examens complémentaires nécessaires

PHASE 2 - VALIDATION GUIDELINES :
- Valide chaque alerte contre guidelines reconnues (Surviving Sepsis, ESC, AHA, etc.)
- Cite systématiquement les sources avec force d'évidence
- Vérifie les contre-indications
- Propose des approches alternatives

PHASE 3 - SCORES DE RISQUE :
- Calcule scores pertinents selon diagnostics (SOFA, qSOFA, APACHE II, GRACE, TIMI, etc.)
- Interprète les résultats et prédit les outcomes
- Évalue la confiance dans les calculs

PHASE 4 - PLAN D'ACTION :
Structure en priorités :
- IMMEDIATE (< 15 min) : actions vitales
- URGENT (< 1h) : actions importantes
- Workup diagnostique priorisé
- Plan de surveillance avec seuils d'alerte
- Consultations spécialisées
- Ajustements médicamenteux avec posologies

PHASE 5 - SYNTHÈSE PREUVES :
- Compilation de toutes les références utilisées
- Déduplication et classification par qualité
- Top recommandations clés

PRINCIPES :
- Toujours privilégier la sécurité patient
- Base toutes tes recommandations sur des guidelines reconnues
- Cite systématiquement tes sources avec force de l'évidence
- Considère les diagnostics graves même si moins probables
- Priorise par urgence : IMMEDIATE > URGENT > ROUTINE
- Vérifie les contre-indications pour chaque recommandation
- Utilise les codes ICD-10 quand applicable
- Confidence score >= 0.7 pour recommandations critiques

QUALITÉ :
- Minimum 3 diagnostics différentiels si pertinent
- Citations avec nom guideline + année + force évidence
- Vérification systématique des interactions médicamenteuses
- Plans d'action concrets et actionnables
"""
)
