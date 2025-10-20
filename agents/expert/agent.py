"""
Agent 3 : Expert/Contextualisation - ADN (AI Diagnostic Navigator)
'Le Professeur de Médecine' - Valide avec guidelines et génère diagnostics différentiels
Temps d'exécution : T+90s à T+120s
"""

import json
from typing import Dict, List, Any
from google.cloud import aiplatform
from vertexai.generative_models import GenerativeModel
from vertexai.preview.generative_models import grounding


class AgentExpert:
    """
    Agent 3 : Expert qui valide les alertes avec des guidelines médicales
    et génère des diagnostics différentiels via RAG
    """
    
    def __init__(self, project_id: str, location: str = "us-central1"):
        self.project_id = project_id
        self.location = location
        aiplatform.init(project=project_id, location=location)
        self.model = GenerativeModel("gemini-2.0-flash")
        
        # Configuration RAG (Vertex AI Search - optionnel si disponible)
        self.rag_disponible = False  # Mettre True si Vertex AI Search configuré
        self.datastore_id = None  # ID du datastore médical si disponible
    
    def analyser_alertes(self, output_agent2: Dict[str, Any]) -> Dict[str, Any]:
        """
        Point d'entrée principal : Analyse l'output de l'Agent 2
        et génère des diagnostics différentiels avec validation
        """
        print("🎓 Agent 3 Expert : Démarrage de l'analyse...")
        
        # Extraction des données importantes
        synthese = output_agent2.get("synthesis", {})
        alertes = output_agent2.get("critical_alerts", [])
        data_patient = output_agent2.get("source_data", {}).get("patient_normalized", {})
        scores = output_agent2.get("clinical_scores", [])
        
        # Phase 1 : Générer les diagnostics différentiels
        print("\n📊 Phase 1 : Génération des diagnostics différentiels...")
        diagnostics = self._generer_diagnostics_differentiels(
            synthese, alertes, data_patient, scores
        )
        
        # Phase 2 : Valider chaque alerte avec guidelines
        print("\n📚 Phase 2 : Validation avec guidelines médicales...")
        alertes_validees = self._valider_alertes_avec_guidelines(alertes, data_patient)
        
        # Phase 3 : Calculer scores de risque additionnels
        print("\n🎯 Phase 3 : Calcul des scores de risque...")
        scores_risque = self._calculer_scores_risque_additionnels(
            diagnostics, data_patient
        )
        
        # Phase 4 : Générer plan d'action sourcé
        print("\n💊 Phase 4 : Génération du plan d'action...")
        plan_action = self._generer_plan_action_source(
            alertes_validees, diagnostics, data_patient
        )
        
        # Résultat final
        output = {
            "differential_diagnoses": diagnostics,
            "validated_alerts": alertes_validees,
            "risk_scores": scores_risque,
            "action_plan": plan_action,
            "evidence_summary": self._generer_synthese_preuves(
                diagnostics, alertes_validees
            )
        }
        
        print("\n✅ Agent 3 Expert : Analyse terminée")
        
        return output
    
    def _generer_diagnostics_differentiels(
        self, 
        synthese: Dict, 
        alertes: List[Dict], 
        data_patient: Dict,
        scores: List[Dict]
    ) -> List[Dict]:
        """
        Génère les diagnostics différentiels en utilisant l'IA
        avec recherche dans les guidelines via RAG si disponible
        """
        
        # Construction du contexte clinique
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
        
        # Avec RAG si disponible
        if self.rag_disponible:
            response = self._query_avec_rag(prompt_diagnostics)
        else:
            response = self.model.generate_content(
                prompt_diagnostics,
                generation_config={"response_mime_type": "application/json"}
            )
        
        result = json.loads(response.text)
        return result.get("differential_diagnoses", [])
    
    def _valider_alertes_avec_guidelines(
        self, 
        alertes: List[Dict], 
        data_patient: Dict
    ) -> List[Dict]:
        """
        Valide chaque alerte critique contre les guidelines médicales
        et ajoute des références sourcées
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
            
            if self.rag_disponible:
                response = self._query_avec_rag(prompt_validation)
            else:
                response = self.model.generate_content(
                    prompt_validation,
                    generation_config={"response_mime_type": "application/json"}
                )
            
            validation = json.loads(response.text)
            
            # Combiner l'alerte originale avec la validation
            alerte_validee = {
                **alerte,  # Alerte originale
                "validation": validation  # Ajout de la validation
            }
            
            alertes_validees.append(alerte_validee)
        
        return alertes_validees
    
    def _calculer_scores_risque_additionnels(
        self, 
        diagnostics: List[Dict], 
        data_patient: Dict
    ) -> List[Dict]:
        """
        Calcule des scores de risque additionnels basés sur les diagnostics
        """
        
        prompt_scores = f"""
Tu es un expert en scores cliniques et pronostic.

DIAGNOSTICS RETENUS :
{json.dumps(diagnostics[:3], indent=2, ensure_ascii=False)}  # Top 3

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
        
        response = self.model.generate_content(
            prompt_scores,
            generation_config={"response_mime_type": "application/json"}
        )
        
        result = json.loads(response.text)
        return result.get("risk_scores", [])
    
    def _generer_plan_action_source(
        self,
        alertes_validees: List[Dict],
        diagnostics: List[Dict],
        data_patient: Dict
    ) -> Dict:
        """
        Génère un plan d'action concret et sourcé
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
        
        response = self.model.generate_content(
            prompt_action,
            generation_config={"response_mime_type": "application/json"}
        )
        
        return json.loads(response.text)
    
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
                "sexe": data_patient.get("sex"),
                "antecedents": data_patient.get("medical_history", {}).get("known_conditions", []),
                "medicaments": data_patient.get("medications_current", []),
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
            if nom not in vues:
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
                for ref in references_uniques[:5]  # Top 5
            ]
        }
    
    def _query_avec_rag(self, prompt: str) -> Any:
        """
        Effectue une requête avec RAG (Vertex AI Search)
        UNIQUEMENT si configuré
        """
        
        if not self.rag_disponible or not self.datastore_id:
            # Fallback sur génération normale
            return self.model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
        
        # Configuration du grounding avec Vertex AI Search
        grounding_source = grounding.VertexAISearch(
            datastore=self.datastore_id,
            project=self.project_id,
            location=self.location
        )
        
        # Génération avec grounding
        response = self.model.generate_content(
            prompt,
            generation_config={
                "response_mime_type": "application/json",
                "grounding": grounding_source
            }
        )
        
        return response


# ============================================================================
# FONCTION D'AFFICHAGE DÉTAILLÉ
# ============================================================================

def afficher_resultats_agent3(resultat: Dict, titre: str = "Agent 3 - Expert"):
    """
    Affiche les résultats de l'Agent 3 de manière structurée
    """
    print("\n" + "="*100)
    print(f"🎓 {titre}")
    print("="*100)
    
    # 1. DIAGNOSTICS DIFFÉRENTIELS
    diagnostics = resultat.get("differential_diagnoses", [])
    print("\n┌─────────────────────────────────────────────────────────────┐")
    print(f"│  🔍 DIAGNOSTICS DIFFÉRENTIELS - {len(diagnostics)} identifié(s)    │")
    print("└─────────────────────────────────────────────────────────────┘")
    
    for i, diag in enumerate(diagnostics, 1):
        prob_emoji = "🔴" if diag.get("probability") == "HIGH" else "🟡" if diag.get("probability") == "MEDIUM" else "🟢"
        print(f"\n{prob_emoji} DIAGNOSTIC #{i} - {diag.get('diagnosis', 'N/A')}")
        print(f"   Code ICD-10 : {diag.get('icd10_code', 'N/A')}")
        print(f"   Probabilité : {diag.get('probability', 'N/A')}")
        print(f"   Score confiance : {diag.get('confidence_score', 0):.2f}")
        print(f"   Urgence : {diag.get('urgency', 'N/A')}")
        
        evidence_for = diag.get("supporting_evidence", [])
        if evidence_for:
            print(f"\n   ✅ Arguments POUR ({len(evidence_for)}) :")
            for ev in evidence_for[:3]:  # Top 3
                print(f"      • {ev.get('finding')} (force: {ev.get('strength')})")
        
        evidence_against = diag.get("contradicting_evidence", [])
        if evidence_against:
            print(f"\n   ❌ Arguments CONTRE ({len(evidence_against)}) :")
            for ev in evidence_against[:2]:
                print(f"      • {ev.get('finding')} (impact: {ev.get('impact')})")
        
        tests = diag.get("additional_tests_needed", [])
        if tests:
            print(f"\n   🔬 Examens nécessaires : {', '.join(tests)}")
    
    # 2. ALERTES VALIDÉES
    alertes_val = resultat.get("validated_alerts", [])
    print("\n┌─────────────────────────────────────────────────────────────┐")
    print(f"│  ✅ ALERTES VALIDÉES - {len(alertes_val)} alerte(s)                 │")
    print("└─────────────────────────────────────────────────────────────┘")
    
    for alerte in alertes_val:
        validation = alerte.get("validation", {})
        validated = validation.get("alert_validated", False)
        strength = validation.get("validation_strength", "N/A")
        
        emoji = "✅" if validated else "⚠️"
        print(f"\n{emoji} {alerte.get('type', 'N/A')}")
        print(f"   Validation : {validated} (force: {strength})")
        print(f"   Urgence validée : {validation.get('action_urgency_validated', 'N/A')}")
        
        guidelines = validation.get("guidelines_references", [])
        if guidelines:
            print(f"\n   📚 Guidelines référencées ({len(guidelines)}) :")
            for guide in guidelines[:2]:  # Top 2
                print(f"      • {guide.get('guideline_name')}")
                print(f"        → {guide.get('recommendation', '')[:100]}...")
    
    # 3. PLAN D'ACTION
    plan = resultat.get("action_plan", {})
    print("\n┌─────────────────────────────────────────────────────────────┐")
    print("│  💊 PLAN D'ACTION                                            │")
    print("└─────────────────────────────────────────────────────────────┘")
    
    immediate = plan.get("immediate_actions", [])
    if immediate:
        print(f"\n🚨 ACTIONS IMMÉDIATES ({len(immediate)}) :")
        for action in immediate:
            print(f"   • {action.get('action')}")
            print(f"     ↳ {action.get('justification')}")
    
    urgent = plan.get("urgent_actions", [])
    if urgent:
        print(f"\n⏰ ACTIONS URGENTES ({len(urgent)}) :")
        for action in urgent:
            print(f"   • {action.get('action')} ({action.get('timeframe')})")
    
    monitoring = plan.get("monitoring_plan", [])
    if monitoring:
        print(f"\n📊 SURVEILLANCE ({len(monitoring)}) :")
        for item in monitoring[:3]:
            print(f"   • {item.get('parameter')} - {item.get('frequency')}")
    
    # 4. SYNTHÈSE DES PREUVES
    evidence = resultat.get("evidence_summary", {})
    print("\n┌─────────────────────────────────────────────────────────────┐")
    print("│  📚 SYNTHÈSE DES PREUVES                                     │")
    print("└─────────────────────────────────────────────────────────────┘")
    
    print(f"\n   Total références : {evidence.get('total_references', 0)}")
    
    strength_summary = evidence.get("evidence_strength_summary", {})
    print(f"\n   Qualité des preuves :")
    print(f"      • Haute : {strength_summary.get('high_quality', 0)}")
    print(f"      • Moyenne : {strength_summary.get('moderate_quality', 0)}")
    print(f"      • Basse : {strength_summary.get('low_quality', 0)}")
    
    # 5. JSON COMPLET
    print("\n┌─────────────────────────────────────────────────────────────┐")
    print("│  📄 OUTPUT JSON COMPLET                                      │")
    print("└─────────────────────────────────────────────────────────────┘")
    print("\n```json")
    print(json.dumps(resultat, indent=2, ensure_ascii=False))
    print("```")
    
    print("\n" + "="*100 + "\n")


# ============================================================================
# EXEMPLE D'UTILISATION
# ============================================================================

if __name__ == "__main__":
    
    # Simuler l'output de l'Agent 2
    output_agent2_exemple = {
        "synthesis": {
            "summary": "Femme de 70 ans, sepsis sévère avec hémoculture positive à SARM",
            "key_problems": ["Sepsis sévère", "MRSA bacteremia", "Elevated lactate"],
            "severity": "HIGH",
            "clinical_trajectory": "DETERIORATING"
        },
        "critical_alerts": [
            {
                "type": "CULTURE_NON_TRAITEE",
                "severity": "CRITICAL",
                "finding": "Hémoculture positive à SARM depuis 12h",
                "source": "blood_culture_2024-10-14",
                "clinical_impact": "Sepsis non contrôlé, risque de choc septique",
                "action_required": "Vancomycine ou Linezolid URGENT"
            },
            {
                "type": "HYPOPERFUSION_TISSULAIRE",
                "severity": "HIGH",
                "finding": "Lactate élevé (3.2) non adressé",
                "clinical_impact": "Hypoperfusion tissulaire",
                "action_required": "Remplissage vasculaire 30ml/kg"
            }
        ],
        "source_data": {
            "patient_normalized": {
                "age": 70,
                "sex": "femme",
                "medical_history": {
                    "known_conditions": ["Hypertension", "Diabète Type 2"]
                },
                "vitals_current": {
                    "temperature": 38.5,
                    "heart_rate": 110,
                    "blood_pressure": "145/92"
                },
                "labs": [
                    {"name": "WBC", "value": 18000, "flag": "HIGH"},
                    {"name": "Lactate", "value": 3.2, "flag": "HIGH"}
                ],
                "cultures": [
                    {
                        "status": "POSITIVE",
                        "organism": "MRSA",
                        "resulted": "2024-10-14T14:30:00"
                    }
                ]
            }
        },
        "clinical_scores": [
            {"score_name": "qSOFA", "value": 2, "interpretation": "Risque élevé"}
        ]
    }
    
    # Initialiser l'Agent 3
    agent3 = AgentExpert(project_id="ai-diagnostic-navigator-475316")
    
    # Analyser
    print("="*80)
    print("TEST AGENT 3 : Expert/RAG")
    print("="*80)
    
    resultat_agent3 = agent3.analyser_alertes(output_agent2_exemple)
    
    # Afficher les résultats
    afficher_resultats_agent3(resultat_agent3, "Sepsis SARM - Validation Expert")