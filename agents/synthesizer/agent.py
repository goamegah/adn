"""
ADK Synthesizer Agent - ADN (AI Diagnostic Navigator)
'The Double Brain' - Summarizes then self-criticizes to find inconsistencies
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from google import genai
from google.genai import types
from google.adk.agents import LlmAgent

from dotenv import load_dotenv
ENV_PATH = Path(__file__).parent.parent / ".env"  # agents/.env (for, local testing)
load_dotenv(dotenv_path=ENV_PATH, override=True)

class AgentSynthetiseur:
    """
    ADK Agent that synthesizes patient data and self-criticizes
    Compatible with ADK interface and hospital/EMS format
    """

    def __init__(self):
        """Initializes the agent with the Gemini client"""
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.client = genai.Client(api_key=self.api_key)
        self.model_id = "gemini-2.0-flash-exp"
        
    def normaliser_input(self, data_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalizes any input format into a unified format
        Handles: hospital format, EMS calls, or any other format
        """
        # If already in the correct format (patient_normalized exists)
        if "patient_normalized" in data_input:
            return data_input

        # If it's an EMS call (with input.text and expected_output)
        if "input" in data_input and "expected_output" in data_input:
            return self._convertir_format_samu(data_input)

        # Otherwise, try to auto-detect
        return self._auto_detecter_format(data_input)

    def _convertir_format_samu(self, data_samu: Dict) -> Dict:
        """Converts EMS format to unified format"""
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
        """Automatically detects format and converts"""
        prompt_detection = f"""
You receive patient data in an unknown format.

RAW DATA:
{json.dumps(data, indent=2, ensure_ascii=False)}

Your mission: Identify and extract ALL relevant medical information.

Output format (STRICT JSON):
{{
    "patient_normalized": {{
        "id": "identifier or generated",
        "source_type": "detected source type",
        "age": numeric_age,
        "sex": "male/female/unknown",
        "admission": {{
            "type": "admission type",
            "chief_complaint": "main reason",
            "date": "date if available"
        }},
        "vitals_current": {{
            "consciousness": "consciousness state",
            "breathing": "respiration",
            "pulse": "pulse",
            "blood_pressure": "blood pressure",
            "temperature": "temperature",
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

Extract EVERYTHING that is available, even if incomplete.
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
        PHASE 1 - Jekyll Mode: Standard Summary
        The AI naturally creates a summary
        """
        prompt_synthese = f"""
You are an experienced emergency physician.

Here is ALL available data for this patient:
{json.dumps(data_patient, indent=2, ensure_ascii=False)}

Your task: Create a professional and structured clinical summary.

Expected format (JSON):
{{
    "summary": "Narrative summary in 3-5 lines of the clinical picture",
    "key_problems": ["Problem 1", "Problem 2", ...],
    "severity": "LOW/MEDIUM/HIGH/CRITICAL",
    "clinical_trajectory": "STABLE/DETERIORATING/IMPROVING"
}}

Be concise but complete. This is a quality standard summary.
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
        PHASE 2 - Hyde Mode: Ruthless Self-Criticism
        """
        prompt_critique = f"""
You are now a senior ultra-demanding auditor physician.
Your job: CHALLENGE EVERYTHING in the summary below!

COMPLETE PATIENT DATA:
{json.dumps(data_patient, indent=2, ensure_ascii=False)}

SUMMARY TO CRITIQUE:
{json.dumps(synthese, indent=2, ensure_ascii=False)}

Your RUTHLESS SELF-CRITICISM mission:
1. Look for what is MISSING in the data
2. Find INCONSISTENCIES between data points
3. Detect ABNORMAL DELAYS
4. Identify UNMENTIONED RISKS
5. Spot INAPPROPRIATE TREATMENTS

Output format (JSON):
{{
    "critical_alerts": [
        {{
            "type": "MISSING_DATA|INCONSISTENCY|DELAYED_ACTION|TREATMENT_MISMATCH|SILENT_DETERIORATION",
            "severity": "LOW/MEDIUM/HIGH/CRITICAL",
            "finding": "Precise description of the problem",
            "action_required": "Required immediate action"
        }}
    ],
    "data_inconsistencies": [
        {{
            "field_1": "field name",
            "value_1": "value",
            "field_2": "field name",
            "value_2": "value",
            "explanation": "Why these values are inconsistent"
        }}
    ],
    "reliability_assessment": {{
        "dossier_completeness": 0.0-1.0,
        "confidence_level": "LOW/MEDIUM/HIGH",
        "critical_data_missing": ["missing data 1", "missing data 2"],
        "data_quality_issues": ["issue 1", "issue 2"]
    }},
    "clinical_scores": [
        {{
            "score_name": "SOFA/qSOFA/NEWS/GCS/etc",
            "value": "calculated score",
            "interpretation": "interpretation",
            "evidence": ["Evidence 1", "Evidence 2"]
        }}
    ],
    "deterioration_analysis": {{
        "risk_level": "LOW/MEDIUM/HIGH/CRITICAL",
        "warning_signs": ["sign 1", "sign 2"],
        "predicted_timeline": "when deterioration might occur",
        "evidence": ["Evidence 1", "Evidence 2"]
    }}
}}

Be RUTHLESS. A life is at stake!
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
        Complete pipeline: Normalization → Synthesis → Critique
        Main entry point of the agent
        """
        # Step 0: Normalize input
        data_normalized = self.normaliser_input(data_input)
        patient_data = data_normalized.get("patient_normalized", {})

        # Step 1: Jekyll Phase (Synthesis)
        synthese = self.phase_synthese(patient_data)

        # Step 2: Hyde Phase (Critique)
        critique = self.phase_critique(patient_data, synthese)

        # Step 3: Merge results
        resultat_final = {
            "agent_type": "SYNTHETISEUR_CRITIQUE",
            "patient_id": patient_data.get("id", "UNKNOWN"),
            "source_type": patient_data.get("source_type", "UNKNOWN"),
            
            # Jekyll Phase
            "synthesis": synthese,
            
            # Hyde Phase
            "critical_alerts": critique.get("critical_alerts", []),
            "data_inconsistencies": critique.get("data_inconsistencies", []),
            "reliability_assessment": critique.get("reliability_assessment", {}),
            "clinical_scores": critique.get("clinical_scores", []),
            "deterioration_analysis": critique.get("deterioration_analysis", {}),
            
            # Preserved raw data
            "raw_patient_data": patient_data
        }

        return resultat_final


def format_output_for_ui(resultat: Dict[str, Any]) -> str:
    """
    Formats the result for display in the ADK interface
    """
    output = []
    
    # Header
    output.append("=" * 80)
    output.append(f"🏥 SYNTHESIZER AGENT - Patient Analysis {resultat.get('patient_id', 'N/A')}")
    output.append("=" * 80)
    
    # Summary
    synthese = resultat.get('synthesis', {})
    output.append("\n📋 CLINICAL SUMMARY")
    output.append("-" * 80)
    output.append(f"{synthese.get('summary', 'N/A')}")
    output.append(f"\n🎯 Severity: {synthese.get('severity', 'N/A')}")
    output.append(f"📊 Trajectory: {synthese.get('clinical_trajectory', 'N/A')}")
    
    if synthese.get('key_problems'):
        output.append("\n⚠️  Key problems:")
        for problem in synthese['key_problems']:
            output.append(f"   • {problem}")
    
    # Critical alerts
    alertes = resultat.get('critical_alerts', [])
    if alertes:
        output.append("\n\n🚨 CRITICAL ALERTS")
        output.append("-" * 80)
        for i, alerte in enumerate(alertes, 1):
            emoji = "🔴" if alerte.get('severity') == 'CRITICAL' else "🟡"
            output.append(f"\n{emoji} Alert #{i} - {alerte.get('type', 'N/A')}")
            output.append(f"   Severity: {alerte.get('severity', 'N/A')}")
            output.append(f"   Finding: {alerte.get('finding', 'N/A')}")
            output.append(f"   💊 Action: {alerte.get('action_required', 'N/A')}")
    
    # Reliability assessment
    reliability = resultat.get('reliability_assessment', {})
    if reliability:
        output.append("\n\n🔍 RELIABILITY ASSESSMENT")
        output.append("-" * 80)
        completeness = reliability.get('dossier_completeness', 0)
        output.append(f"📊 Completeness: {completeness:.0%}")
        output.append(f"🎯 Confidence: {reliability.get('confidence_level', 'N/A')}")
        
        if reliability.get('critical_data_missing'):
            output.append("\n⚠️  Critical missing data:")
            for data in reliability['critical_data_missing']:
                output.append(f"   ❌ {data}")
    
    # Clinical scores
    scores = resultat.get('clinical_scores', [])
    if scores:
        output.append("\n\n📊 CLINICAL SCORES")
        output.append("-" * 80)
        for score in scores:
            output.append(f"\n📈 {score.get('score_name', 'N/A')}: {score.get('value', 'N/A')}")
            output.append(f"   {score.get('interpretation', 'N/A')}")
    
    output.append("\n" + "=" * 80)
    
    return "\n".join(output)


# ============================================================================
# ADK ROOT AGENT CONFIGURATION
# ============================================================================

root_agent = LlmAgent(
    name="synthetiseur_agent",
    
    model="gemini-2.5-flash",
    
    description="""
Medical synthesis and self-criticism agent using the Jekyll/Hyde method.
Analyzes patient data, creates a synthesis then self-criticizes to detect
inconsistencies, critical alerts and silent deteriorations.

CAPABILITIES:
- Multi-format normalization (hospital, EMS, auto-detection)
- Intelligent clinical synthesis
- Self-criticism and inconsistency detection
- Silent deterioration detection
- Clinical score calculation (SOFA, qSOFA, NEWS, etc.)
- Data reliability assessment
""",
    
    instruction="""
You are an expert medical agent in clinical analysis with two modes of operation:

JEKYLL MODE (Synthesis):
- Creates clear and structured clinical summaries
- Identifies patient key problems
- Evaluates severity and clinical trajectory

HYDE MODE (Critique):
- Ruthlessly challenges data and conclusions
- Detects inconsistencies and missing data
- Identifies non-obvious risks
- Calculates relevant clinical scores
- Predicts potential deteriorations

PRINCIPLES:
- Always prioritize patient safety
- Be precise and factual
- Report any concerning element
- Never invent data
- Adapt analysis to context (pre-hospital emergency vs hospital)

ACCEPTED FORMATS:
1. Hospital format: {"patient_normalized": {...}}
2. EMS format: {"input": {"text": "..."}, "expected_output": {...}}
3. Free text: "Patient aged X years, ..."

ANALYSIS PROCESS:
1. Normalize input (automatically detect format)
2. Jekyll Phase: Create a complete and structured synthesis
3. Hyde Phase: Self-criticize to find flaws
4. Return a complete analysis with priority alerts
"""
)


# Entry point for standalone tests
if __name__ == "__main__":
    # Test example
    test_case = {
        "patient_normalized": {
            "id": "TEST_001",
            "age": 65,
            "admission": {
                "type": "EMERGENCY",
                "chief_complaint": "Chest pain",
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
                    "location": "chest",
                    "intensity": "8/10",
                    "radiation": "left arm"
                }
            }
        }
    }
    
    agent = AgentSynthetiseur()
    result = agent.analyser_patient(test_case)
    print(format_output_for_ui(result))
    print(result)