"""
Agent 3 Expert ADK - ADN (AI Diagnostic Navigator)
'The Medicine Professor' - Validates with guidelines and generates differential diagnoses
Compatible with ADK architecture
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
    Agent 3: Expert that validates alerts with medical guidelines
    and generates differential diagnoses
    Compatible with ADK interface
    """

    def __init__(self):
        """Initialize the agent with Gemini client"""
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.client = genai.Client(api_key=self.api_key)
        self.model_id = "gemini-2.0-flash-exp"
        
        # RAG Configuration (Vertex AI Search - optional if available)
        self.rag_disponible = False
        self.datastore_id = None

    def phase_diagnostics_differentiels(
        self, 
        output_agent2: Dict[str, Any]
    ) -> List[Dict]:
        """
        PHASE 1: Generation of differential diagnoses
        """
        synthese = output_agent2.get("synthesis", {})
        alertes = output_agent2.get("critical_alerts", [])
        data_patient = output_agent2.get("raw_patient_data", {})
        scores = output_agent2.get("clinical_scores", [])
        
        contexte_clinique = self._construire_contexte_clinique(
            synthese, alertes, data_patient, scores
        )
        
        prompt_diagnostics = f"""
You are an expert in emergency medicine and infectious diseases.

COMPLETE CLINICAL CONTEXT:
{json.dumps(contexte_clinique, indent=2, ensure_ascii=False)}

Your mission: Generate a list of relevant differential diagnoses.

For each diagnosis, provide:
1. The diagnosis name
2. The probability (HIGH/MEDIUM/LOW)
3. A confidence score (0.0 to 1.0)
4. Criteria supporting this diagnosis (found in the data)
5. Criteria contradicting this diagnosis
6. Additional tests needed to confirm/rule out

Strict JSON format:
{{
    "differential_diagnoses": [
        {{
            "diagnosis": "Diagnosis name",
            "icd10_code": "ICD-10 code if applicable",
            "probability": "HIGH/MEDIUM/LOW",
            "confidence_score": 0.85,
            "supporting_evidence": [
                {{
                    "finding": "Clinical element",
                    "strength": "DEFINITIVE/STRONG/MODERATE/WEAK",
                    "source": "Where this info comes from"
                }}
            ],
            "contradicting_evidence": [
                {{
                    "finding": "Element that contradicts",
                    "impact": "MAJOR/MODERATE/MINOR"
                }}
            ],
            "additional_tests_needed": [
                "Test 1",
                "Test 2"
            ],
            "urgency": "IMMEDIATE/URGENT/ROUTINE",
            "typical_presentation": "Description of typical presentation",
            "atypical_features": ["Observed atypical feature"]
        }}
    ]
}}

Rank diagnoses by decreasing probability.
Be thorough but relevant - include serious diagnoses even if less probable.
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
        PHASE 2: Validation of alerts against medical guidelines
        """
        alertes_validees = []
        
        for alerte in alertes:
            prompt_validation = f"""
You are an expert in evidence-based medicine.

ALERT TO VALIDATE:
{json.dumps(alerte, indent=2, ensure_ascii=False)}

PATIENT CONTEXT:
{json.dumps(data_patient, indent=2, ensure_ascii=False)}

Your mission: Validate this alert against recognized medical guidelines.

JSON format:
{{
    "alert_validated": true/false,
    "validation_strength": "STRONG/MODERATE/WEAK",
    "guidelines_references": [
        {{
            "guideline_name": "Guideline name (e.g., Surviving Sepsis Campaign 2021)",
            "recommendation": "Exact recommendation",
            "strength_of_evidence": "HIGH/MODERATE/LOW",
            "source_url": "URL if available",
            "quote": "Relevant guideline citation"
        }}
    ],
    "clinical_evidence": [
        {{
            "evidence_type": "RCT/Meta-analysis/Observational/Expert opinion",
            "finding": "Study result",
            "relevance": "Description of relevance for this case"
        }}
    ],
    "action_urgency_validated": "IMMEDIATE/WITHIN_1H/WITHIN_6H/ROUTINE",
    "alternative_approaches": [
        "Alternative approach 1 if the first is not possible"
    ],
    "contraindications_check": {{
        "contraindications_present": false,
        "details": "Contraindication verification"
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
            
            # Combine original alert with validation
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
        PHASE 3: Calculation of additional risk scores
        """
        prompt_scores = f"""
You are an expert in clinical scores and prognosis.

RETAINED DIAGNOSES:
{json.dumps(diagnostics[:3], indent=2, ensure_ascii=False)}

PATIENT DATA:
{json.dumps(data_patient, indent=2, ensure_ascii=False)}

For each diagnosis, calculate relevant risk scores.

Score examples by diagnosis:
- Sepsis: APACHE II, SAPS II, predicted mortality
- ACS: TIMI, GRACE, predicted risk
- Stroke: NIHSS, mRS
- PE: Wells, Geneva, PESI
- Heart Failure: NYHA, Framingham
- Trauma: ISS, RTS, TRISS
- DKA: severity score
- Pancreatitis: Ranson, BISAP

Strict JSON format:
{{
    "risk_scores": [
        {{
            "diagnosis": "Associated diagnosis",
            "score_name": "Score name (e.g., APACHE II)",
            "score_value": "Calculated value",
            "score_components": [
                {{
                    "component": "Age",
                    "value": 65,
                    "points": 5,
                    "explanation": "Age > 65 years = 5 points"
                }}
            ],
            "risk_category": "LOW/MODERATE/HIGH/CRITICAL",
            "predicted_outcome": {{
                "mortality_24h": "X%",
                "mortality_7d": "X%",
                "mortality_30d": "X%",
                "other_outcome": "Description"
            }},
            "interpretation": "Clinical interpretation",
            "confidence_in_calculation": "HIGH/MODERATE/LOW",
            "missing_data_impact": "Impact of missing data on accuracy"
        }}
    ]
}}

Calculate ONLY applicable and useful scores.
Indicate confidence and impact of missing data.
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
        output_agent2: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        PHASE 4: Generation of prioritized action plan
        """
        # Extract relevant data
        diagnostics = output_agent2.get("differential_diagnoses", [])
        alertes_validees = output_agent2.get("validated_alerts", [])
        scores = output_agent2.get("risk_scores", [])
        data_patient = output_agent2.get("raw_patient_data", {})
        
        prompt_plan = f"""
You are an expert in emergency medicine and critical care.

CLINICAL CONTEXT:
- Top Diagnoses: {json.dumps(diagnostics[:3], indent=2, ensure_ascii=False)}
- Validated Alerts: {json.dumps(alertes_validees, indent=2, ensure_ascii=False)}
- Risk Scores: {json.dumps(scores, indent=2, ensure_ascii=False)}
- Patient Data: {json.dumps(data_patient, indent=2, ensure_ascii=False)}

Your mission: Generate a comprehensive, prioritized, and evidence-based action plan.

Strict JSON format:
{{
    "action_plan": {{
        "immediate_actions": [
            {{
                "priority": 1,
                "action": "Precise action",
                "timeframe": "< 15 minutes",
                "justification": "Why this action is critical",
                "guideline_reference": "Guideline supporting this action",
                "monitoring_after_action": "What to monitor"
            }}
        ],
        "urgent_actions": [
            {{
                "priority": 2,
                "action": "Action",
                "timeframe": "< 1 hour",
                "justification": "Justification",
                "guideline_reference": "Reference"
            }}
        ],
        "diagnostic_workup": [
            {{
                "test": "Test name",
                "priority": "STAT/URGENT/ROUTINE",
                "rationale": "Why this test",
                "expected_findings": "What we expect to find",
                "impact_on_management": "How it changes management"
            }}
        ],
        "monitoring_plan": [
            {{
                "parameter": "Parameter to monitor",
                "frequency": "Frequency",
                "alert_threshold": "Value triggering alert",
                "action_if_threshold": "Action if threshold reached"
            }}
        ],
        "specialist_consultations": [
            {{
                "specialty": "Specialty",
                "urgency": "IMMEDIATE/URGENT/ROUTINE",
                "reason": "Reason for consultation",
                "specific_questions": "Specific questions for specialist"
            }}
        ],
        "medication_adjustments": [
            {{
                "medication": "Medication name",
                "action": "START/STOP/ADJUST",
                "dose": "Precise dose",
                "route": "Route",
                "frequency": "Frequency",
                "rationale": "Why this change",
                "contraindication_check": "Verified contraindications",
                "monitoring": "What to monitor"
            }}
        ],
        "disposition": {{
            "recommended_level_of_care": "ICU/Step-down/Floor/Discharge",
            "justification": "Why this level of care",
            "alternative_if_unavailable": "Alternative if not available"
        }}
    }}
}}

PRIORITIES:
1. IMMEDIATE actions (< 15 min): life-saving
2. URGENT actions (< 1h): important for outcome
3. ROUTINE: can wait but necessary

Base ALL recommendations on recognized guidelines.
Verify contraindications for EVERY recommendation.
"""
        
        response = self.client.models.generate_content(
            model=self.model_id,
            contents=prompt_plan,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        
        result = json.loads(response.text)
        return result.get("action_plan", {})

    def phase_synthese_preuves(
        self, 
        validated_alerts: List[Dict],
        action_plan: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        PHASE 5: Synthesis of all evidence and medical references used
        """
        # Collect all references from validated alerts
        all_references = []
        
        for alert in validated_alerts:
            validation = alert.get("validation", {})
            guidelines = validation.get("guidelines_references", [])
            all_references.extend(guidelines)
        
        # Deduplicate and classify by quality
        unique_refs = {}
        for ref in all_references:
            ref_name = ref.get("guideline_name", "")
            if ref_name and ref_name not in unique_refs:
                unique_refs[ref_name] = ref
        
        # Count by evidence strength
        high_quality = sum(
            1 for ref in unique_refs.values() 
            if ref.get("strength_of_evidence") == "HIGH"
        )
        moderate_quality = sum(
            1 for ref in unique_refs.values() 
            if ref.get("strength_of_evidence") == "MODERATE"
        )
        low_quality = sum(
            1 for ref in unique_refs.values() 
            if ref.get("strength_of_evidence") == "LOW"
        )
        
        return {
            "total_references": len(unique_refs),
            "references": list(unique_refs.values()),
            "evidence_strength_summary": {
                "high_quality": high_quality,
                "moderate_quality": moderate_quality,
                "low_quality": low_quality
            },
            "key_recommendations": [
                ref.get("recommendation") 
                for ref in unique_refs.values() 
                if ref.get("recommendation")
            ]
        }

    def _construire_contexte_clinique(
        self,
        synthese: Dict,
        alertes: List[Dict],
        data_patient: Dict,
        scores: List[Dict]
    ) -> Dict[str, Any]:
        """
        Build complete clinical context for the LLM
        """
        return {
            "synthesis": synthese,
            "critical_alerts": alertes,
            "patient_data": data_patient,
            "clinical_scores": scores
        }

    def analyser_complet(
        self, 
        output_agent2: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Complete analysis: executes all 5 phases
        
        Args:
            output_agent2: Complete output from Agent 2 (Synthesizer)
            
        Returns:
            Complete result with diagnoses, validations, scores, plan, and evidence
        """
        print("\n" + "="*100)
        print("🎓 AGENT 3 - EXPERT MEDICAL VALIDATOR")
        print("="*100)
        
        # PHASE 1: Differential diagnoses
        print("\n📋 PHASE 1 - Generating differential diagnoses...")
        diagnostics = self.phase_diagnostics_differentiels(output_agent2)
        print(f"   ✅ {len(diagnostics)} diagnoses generated")
        
        # PHASE 2: Guideline validation
        print("\n📚 PHASE 2 - Validating alerts against guidelines...")
        alertes = output_agent2.get("critical_alerts", [])
        data_patient = output_agent2.get("raw_patient_data", {})
        alertes_validees = self.phase_validation_guidelines(alertes, data_patient)
        print(f"   ✅ {len(alertes_validees)} alerts validated")
        
        # PHASE 3: Risk scores
        print("\n🎯 PHASE 3 - Calculating risk scores...")
        scores = self.phase_scores_risque(diagnostics, data_patient)
        print(f"   ✅ {len(scores)} scores calculated")
        
        # PHASE 4: Action plan
        print("\n💊 PHASE 4 - Generating action plan...")
        
        # Prepare enriched data for action plan
        enriched_data = {
            **output_agent2,
            "differential_diagnoses": diagnostics,
            "validated_alerts": alertes_validees,
            "risk_scores": scores
        }
        
        plan_action = self.phase_plan_action(enriched_data)
        print(f"   ✅ Action plan generated")
        
        # PHASE 5: Evidence synthesis
        print("\n📊 PHASE 5 - Synthesizing evidence...")
        synthese_preuves = self.phase_synthese_preuves(alertes_validees, plan_action)
        print(f"   ✅ {synthese_preuves['total_references']} references compiled")
        
        # Assemble complete result
        result = {
            "patient_id": output_agent2.get("patient_id"),
            "differential_diagnoses": diagnostics,
            "validated_alerts": alertes_validees,
            "risk_scores": scores,
            "action_plan": plan_action,
            "evidence_summary": synthese_preuves
        }
        
        print("\n" + "="*100)
        print("✅ COMPLETE ANALYSIS FINISHED")
        print("="*100 + "\n")
        
        return result


def format_output_for_ui(resultat: Dict[str, Any]) -> str:
    """
    Format the result for display in ADK interface
    """
    output = []
    
    # Header
    output.append("=" * 100)
    output.append(f"🎓 EXPERT AGENT - Medical Validation Patient {resultat.get('patient_id', 'N/A')}")
    output.append("=" * 100)
    
    # 1. DIFFERENTIAL DIAGNOSES
    diagnostics = resultat.get("differential_diagnoses", [])
    output.append(f"\n┌{'─'*98}┐")
    output.append(f"│  🔍 DIFFERENTIAL DIAGNOSES - {len(diagnostics)} identified{' '*(98-len(f'  🔍 DIFFERENTIAL DIAGNOSES - {len(diagnostics)} identified'))}│")
    output.append(f"└{'─'*98}┘")
    
    for i, diag in enumerate(diagnostics, 1):
        prob_emoji = "🔴" if diag.get("probability") == "HIGH" else "🟡" if diag.get("probability") == "MEDIUM" else "🟢"
        output.append(f"\n{prob_emoji} DIAGNOSIS #{i} - {diag.get('diagnosis', 'N/A')}")
        output.append(f"   ICD-10 Code: {diag.get('icd10_code', 'N/A')}")
        output.append(f"   Probability: {diag.get('probability', 'N/A')} | Confidence: {diag.get('confidence_score', 0):.2f}")
        output.append(f"   Urgency: {diag.get('urgency', 'N/A')}")
        
        evidence_for = diag.get("supporting_evidence", [])
        if evidence_for:
            output.append(f"\n   ✅ Supporting Evidence ({len(evidence_for)}):")
            for ev in evidence_for[:3]:
                output.append(f"      • {ev.get('finding')} (strength: {ev.get('strength')})")
        
        evidence_against = diag.get("contradicting_evidence", [])
        if evidence_against:
            output.append(f"\n   ❌ Contradicting Evidence ({len(evidence_against)}):")
            for ev in evidence_against[:2]:
                output.append(f"      • {ev.get('finding')} (impact: {ev.get('impact')})")
        
        tests = diag.get("additional_tests_needed", [])
        if tests:
            output.append(f"\n   🔬 Required Tests: {', '.join(tests[:3])}")
    
    # 2. VALIDATED ALERTS
    alertes_val = resultat.get("validated_alerts", [])
    output.append(f"\n\n┌{'─'*98}┐")
    output.append(f"│  ✅ VALIDATED ALERTS - {len(alertes_val)} alert(s){' '*(98-len(f'  ✅ VALIDATED ALERTS - {len(alertes_val)} alert(s)'))}│")
    output.append(f"└{'─'*98}┘")
    
    for alerte in alertes_val:
        validation = alerte.get("validation", {})
        validated = validation.get("alert_validated", False)
        strength = validation.get("validation_strength", "N/A")
        
        emoji = "✅" if validated else "⚠️"
        output.append(f"\n{emoji} {alerte.get('type', 'N/A')}")
        output.append(f"   Finding: {alerte.get('finding', 'N/A')}")
        output.append(f"   Validation: {validated} (strength: {strength})")
        output.append(f"   Urgency: {validation.get('action_urgency_validated', 'N/A')}")
        
        guidelines = validation.get("guidelines_references", [])
        if guidelines:
            output.append(f"\n   📚 Guidelines ({len(guidelines)}):")
            for guide in guidelines[:2]:
                output.append(f"      • {guide.get('guideline_name')}")
                rec = guide.get('recommendation', '')
                if rec:
                    output.append(f"        → {rec[:80]}...")
    
    # 3. ACTION PLAN
    plan = resultat.get("action_plan", {})
    output.append(f"\n\n┌{'─'*98}┐")
    output.append(f"│  💊 ACTION PLAN{' '*83}│")
    output.append(f"└{'─'*98}┘")
    
    immediate = plan.get("immediate_actions", [])
    if immediate:
        output.append(f"\n🚨 IMMEDIATE ACTIONS (< 15 min) - {len(immediate)} action(s):")
        for action in immediate:
            output.append(f"   • {action.get('action')}")
            output.append(f"     ↳ {action.get('justification')}")
    
    urgent = plan.get("urgent_actions", [])
    if urgent:
        output.append(f"\n⏰ URGENT ACTIONS (< 1h) - {len(urgent)} action(s):")
        for action in urgent:
            output.append(f"   • {action.get('action')} - {action.get('timeframe')}")
    
    monitoring = plan.get("monitoring_plan", [])
    if monitoring:
        output.append(f"\n📊 MONITORING - {len(monitoring)} parameter(s):")
        for item in monitoring[:3]:
            output.append(f"   • {item.get('parameter')} - {item.get('frequency')}")
    
    # 4. RISK SCORES
    scores = resultat.get("risk_scores", [])
    if scores:
        output.append(f"\n\n┌{'─'*98}┐")
        output.append(f"│  🎯 RISK SCORES - {len(scores)} score(s){' '*(98-len(f'  🎯 RISK SCORES - {len(scores)} score(s)'))}│")
        output.append(f"└{'─'*98}┘")
        
        for score in scores:
            output.append(f"\n📈 {score.get('score_name', 'N/A')}: {score.get('score_value', 'N/A')}")
            output.append(f"   Category: {score.get('risk_category', 'N/A')}")
            output.append(f"   Interpretation: {score.get('interpretation', 'N/A')}")
    
    # 5. EVIDENCE SYNTHESIS
    evidence = resultat.get("evidence_summary", {})
    output.append(f"\n\n┌{'─'*98}┐")
    output.append(f"│  📚 EVIDENCE SYNTHESIS{' '*73}│")
    output.append(f"└{'─'*98}┘")
    
    output.append(f"\n📊 Total References: {evidence.get('total_references', 0)}")
    
    strength_summary = evidence.get("evidence_strength_summary", {})
    if strength_summary:
        output.append(f"\n🎯 Evidence Quality:")
        output.append(f"   • High: {strength_summary.get('high_quality', 0)}")
        output.append(f"   • Moderate: {strength_summary.get('moderate_quality', 0)}")
        output.append(f"   • Low: {strength_summary.get('low_quality', 0)}")
    
    output.append("\n" + "=" * 100)
    
    return "\n".join(output)


# ============================================================================
# ADK ROOT AGENT CONFIGURATION
# ============================================================================

root_agent = LlmAgent(
    name="expert_agent",
    
    model="gemini-2.0-flash-exp",
    
    description="""
Expert medical agent in clinical validation and differential diagnoses.
Analyzes alerts from the Synthesizer Agent, validates against medical guidelines,
generates differential diagnoses and proposes evidence-based action plans.

CAPABILITIES:
- Generation of differential diagnoses with evidence
- Validation of alerts against international guidelines
- Calculation of specialized risk scores (APACHE II, GRACE, TIMI, NIHSS, etc.)
- Generation of prioritized and evidence-based action plans
- Synthesis of evidence and medical references
""",
    
    instruction="""
You are a medical professor expert in emergency medicine and infectious diseases.

ROLE:
- Validate clinical alerts against recognized medical guidelines
- Generate evidence-based differential diagnoses
- Calculate relevant risk scores
- Propose evidence-based and prioritized action plans

5-PHASE PROCESS:

PHASE 1 - DIFFERENTIAL DIAGNOSES:
- Generate a complete and relevant list of diagnoses
- For each diagnosis: probability, confidence, evidence FOR/AGAINST
- Include serious diagnoses even if less probable
- Identify necessary additional tests

PHASE 2 - GUIDELINE VALIDATION:
- Validate each alert against recognized guidelines (Surviving Sepsis, ESC, AHA, etc.)
- Systematically cite sources with strength of evidence
- Verify contraindications
- Propose alternative approaches

PHASE 3 - RISK SCORES:
- Calculate relevant scores based on diagnoses (SOFA, qSOFA, APACHE II, GRACE, TIMI, etc.)
- Interpret results and predict outcomes
- Evaluate confidence in calculations

PHASE 4 - ACTION PLAN:
Structure by priorities:
- IMMEDIATE (< 15 min): life-saving actions
- URGENT (< 1h): important actions
- Prioritized diagnostic workup
- Monitoring plan with alert thresholds
- Specialized consultations
- Medication adjustments with dosages

PHASE 5 - EVIDENCE SYNTHESIS:
- Compilation of all references used
- Deduplication and classification by quality
- Top key recommendations

PRINCIPLES:
- Always prioritize patient safety
- Base all recommendations on recognized guidelines
- Systematically cite sources with strength of evidence
- Consider serious diagnoses even if less probable
- Prioritize by urgency: IMMEDIATE > URGENT > ROUTINE
- Verify contraindications for each recommendation
- Use ICD-10 codes when applicable
- Confidence score >= 0.7 for critical recommendations

QUALITY:
- Minimum 3 differential diagnoses if relevant
- Citations with guideline name + year + strength of evidence
- Systematic verification of drug interactions
- Concrete and actionable action plans
"""
)