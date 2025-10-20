# backend/app/routes/orchestrator_routes.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import time
import logging
import sys
import os

# Ajouter le chemin racine pour importer les agents
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from agents.orchestrator.agent import OrchestrateurADN

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["orchestrator"])

# Initialiser l'orchestrateur (une seule fois au démarrage)
PROJECT_ID = os.getenv("GCP_PROJECT_ID", "ai-diagnostic-navigator-475316")
orchestrateur = OrchestrateurADN(project_id=PROJECT_ID)


class AnalyzeRequest(BaseModel):
    patient_id: Optional[str] = None  # ID patient MIMIC-III ou None
    query: str  # Texte médical OU question
    metadata: Dict[str, Any] = {}


class AnalyzeResponse(BaseModel):
    analysis_id: str
    confidence: float
    processing_time_ms: int
    patient_summary: Dict[str, Any]
    differentials: List[Dict[str, Any]]
    alerts: List[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]
    chat_reply: str


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(req: AnalyzeRequest):
    """
    Endpoint principal d'analyse avec les VRAIS agents ADN
    - Si patient_id fourni : charge depuis MIMIC-III
    - Sinon : analyse le texte médical dans query
    """
    start_time = time.time()
    
    if not req.query and not req.patient_id:
        raise HTTPException(status_code=400, detail="query ou patient_id requis")

    logger.info(f"🚀 Analyse orchestrée - Patient: {req.patient_id}, Query length: {len(req.query)}")

    try:
        # Déterminer le mode (MIMIC-III ou texte médical)
        if req.patient_id and req.patient_id.isdigit():
            # Mode MIMIC-III
            subject_id = int(req.patient_id)
            resultat = orchestrateur.analyser_patient(subject_id)
            analysis_id = f"mimic_{subject_id}_{int(time.time())}"
        else:
            # Mode texte médical
            from agents.collector.agent import AgentCollecteur
            from agents.synthesizer.agent import AgentSynthetiseur
            from agents.expert.agent import AgentExpert
            
            agent1 = AgentCollecteur()
            agent2 = AgentSynthetiseur(project_id=PROJECT_ID)
            agent3 = AgentExpert(project_id=PROJECT_ID)
            
            # Étape 1 : Collecte depuis texte
            data_collectee = agent1.collecter_donnees_patient(texte_medical=req.query)
            
            # Étape 2 : Synthèse + Critique
            resultat_synthese = agent2.analyser_patient(data_collectee)
            
            # Étape 3 : Expertise
            resultat_expert = agent3.analyser_alertes(resultat_synthese)
            
            resultat = {
                "patient_id": "TEXT_INPUT",
                "agent1_collecteur": data_collectee,
                "agent2_synthetiseur": resultat_synthese,
                "agent3_expert": resultat_expert,
                "status": "success"
            }
            analysis_id = f"text_{int(time.time())}"
        
        # Formater la réponse pour le frontend
        response = _formater_pour_frontend(resultat)
        response["analysis_id"] = analysis_id
        response["processing_time_ms"] = int((time.time() - start_time) * 1000)
        
        logger.info(f"✅ Analyse terminée: {analysis_id} en {response['processing_time_ms']}ms")
        
        return AnalyzeResponse(**response)
    
    except Exception as e:
        logger.error(f"❌ Erreur analyse: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")


def _formater_pour_frontend(resultat: Dict) -> Dict:
    """Convertit le format agent → format frontend"""
    
    # Extraire les données des agents
    agent1 = resultat.get("agent1_collecteur", {}).get("patient_normalized", {})
    agent2 = resultat.get("agent2_synthetiseur", {})
    agent3 = resultat.get("agent3_expert", {})
    
    synthesis = agent2.get("synthesis", {})
    
    # Formater patient_summary
    patient_summary = {
        "patient": {
            "name": f"Patient {agent1.get('id', 'N/A')}",
            "age": agent1.get("age")
        },
        "admission": {
            "reason": agent1.get("admission", {}).get("chief_complaint", "Texte médical"),
            "time": str(agent1.get("admission", {}).get("date", ""))
        },
        "synthesis_text": synthesis.get("summary", "Analyse en cours..."),
        "vital_signs": agent1.get("vitals_current", {})
    }
    
    # Si c'est un texte médical, ajouter le texte brut
    if agent1.get("source_type") == "TEXTE_MEDICAL":
        patient_summary["raw_text"] = agent1.get("texte_brut", "")
    
    # Formater diagnostics différentiels
    differentials_raw = agent3.get("differential_diagnoses", [])
    differentials = []
    for dx in differentials_raw:
        differentials.append({
            "pathology": dx.get("diagnosis", "N/A"),
            "probability_label": dx.get("probability", "N/A"),
            "score": dx.get("confidence_score", 0) * 10,  # Convertir 0-1 en 0-10
            "evidence": [
                {"text": ev.get("finding", ""), "source": ev.get("source", "")}
                for ev in dx.get("supporting_evidence", [])
            ],
            "suggested_actions": [
                {"priority": i+1, "action": action}
                for i, action in enumerate(dx.get("additional_tests_needed", []))
            ]
        })
    
    # Formater alertes
    alerts_raw = agent2.get("critical_alerts", [])
    alerts = []
    for alert in alerts_raw:
        alerts.append({
            "severity": alert.get("severity", "warning").lower(),
            "title": alert.get("type", "Alerte"),
            "description": alert.get("finding", ""),
            "confidence": 0.9
        })
    
    # Formater recommandations
    actions_raw = agent3.get("action_plan", {}).get("immediate_actions", [])
    recommendations = []
    for i, action in enumerate(actions_raw, 1):
        recommendations.append({
            "priority": i,
            "category": "Action Urgente" if i == 1 else "Monitoring",
            "title": action.get("action", "Action recommandée")[:50],
            "description": action.get("justification", ""),
            "expected_delay": "< 1h"
        })
    
    # Message chat
    nb_diagnostics = len(differentials)
    nb_alertes = len(alerts)
    severity = synthesis.get("severity", "N/A")
    
    chat_reply = (
        f"✅ Analyse complétée\n\n"
        f"📊 Sévérité: {severity}\n"
        f"🧠 {nb_diagnostics} diagnostics différentiels identifiés\n"
        f"🚨 {nb_alertes} alertes critiques détectées\n\n"
        f"Consultez les panels pour les détails complets."
    )
    
    return {
        "confidence": 0.88,
        "patient_summary": patient_summary,
        "differentials": differentials,
        "alerts": alerts,
        "recommendations": recommendations,
        "chat_reply": chat_reply
    }


@router.get("/status")
async def orchestrator_status():
    """Health check de l'orchestrateur"""
    return {
        "service": "ADN Orchestrator",
        "status": "operational",
        "version": "3.0.0",
        "agents": {
            "collector": {"status": "active", "modes": ["MIMIC-III", "Texte médical"]},
            "synthesizer": {"status": "active", "description": "Synthèse Jekyll/Hyde"},
            "expert": {"status": "active", "description": "Diagnostics + RAG"},
        }
    }