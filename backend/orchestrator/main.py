from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any
import time
import random

app = FastAPI(title="ADN Orchestrator - Mock")

# Allow CORS from local dev frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {
        "service": "ADN Orchestrator",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "analyze": "/api/analyze",
            "health": "/health"
        }
    }


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "adn-orchestrator"}


class AnalyzeRequest(BaseModel):
    patient_id: str = ""
    query: str
    metadata: Dict[str, Any] = {}


class AnalyzeResponse(BaseModel):
    analysis_id: str = "ana_demo_001"
    confidence: float = 0.87
    processing_time_ms: int = 1850
    patient_summary: Dict[str, Any]
    differentials: List[Dict[str, Any]]
    alerts: List[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]
    chat_reply: str


@app.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze(req: AnalyzeRequest):
    # This is a mock implementation. Replace with orchestration logic.
    start_time = time.time()
    
    if not req.query:
        raise HTTPException(status_code=400, detail="query is required")

    # Générer un ID d'analyse unique
    analysis_id = f"ana_{random.randint(100000, 999999)}"
    
    # Simulated synthesized patient summary (format moderne)
    patient_summary = {
        "patient": {
            "name": "Marie Dubois",
            "age": 65
        },
        "admission": {
            "reason": "Dyspnée aiguë",
            "time": "14:15"
        },
        "allergies": [
            {"substance": "Pénicilline", "severity": "severe"}
        ],
        "antecedents": [
            {"pathology": "Hypertension", "year": 2019},
            {"pathology": "Diabète Type 2", "year": 2021},
            {"pathology": "Fibrillation auriculaire", "year": 2023}
        ],
        "current_medications": [
            {"drug": "Metformine", "dosage": "1000mg"},
            {"drug": "Bisoprolol", "dosage": "5mg"},
            {"drug": "Apixaban", "dosage": "5mg"}
        ],
        "vital_signs": {
            "blood_pressure": {"systolic": 145, "diastolic": 92},
            "heart_rate": {"value": 110, "rhythm": "irrégulier"},
            "spo2": {"value": 89},
            "temperature": {"value": 37.8}
        }
    }

    differentials = [
        {
            "pathology": "Embolie Pulmonaire",
            "probability_label": "Élevée",
            "score": 7.5,
            "evidence": [
                {"text": "Dyspnée aiguë + ATCD TVP", "source": "DPI"},
                {"text": "D-dimères très élevés (2850)", "source": "LIS"},
                {"text": "FA connue", "source": "DPI"}
            ],
            "suggested_actions": [
                {"priority": 1, "action": "Angio-TDM thoracique en urgence"}
            ]
        },
        {
            "pathology": "Décompensation Cardiaque",
            "probability_label": "Moyenne",
            "score": 5.2,
            "evidence": [
                {"text": "FA + Dyspnée", "source": "DPI"},
                {"text": "HTA connue", "source": "DPI"}
            ],
            "suggested_actions": [
                {"priority": 2, "action": "ECG, Rx Thorax, NT-proBNP"}
            ]
        },
        {
            "pathology": "Pneumonie Atypique",
            "probability_label": "Faible",
            "score": 3.1,
            "evidence": [
                {"text": "Fébricule + Dyspnée", "source": "Examen"},
                {"text": "CRP normale ce matin", "source": "LIS"}
            ],
            "suggested_actions": [
                {"priority": 3, "action": "Rx Thorax si autres causes exclues"}
            ]
        },
    ]

    alerts = [
        {
            "severity": "critical",
            "title": "Antécédent de TVP Non Répertorié",
            "description": "Thrombose veineuse profonde documentée en 2018 (Note infirmière du 15/03/2018) absente de la liste des diagnostics actifs. Risque élevé d'embolie pulmonaire.",
            "confidence": 0.95
        },
        {
            "severity": "warning",
            "title": "D-Dimères Élevés Non Signalés",
            "description": "Résultat laboratoire ce matin: D-Dimères à 2850 ng/mL (N < 500). Non mentionnés dans le rapport d'admission.",
            "confidence": 1.0
        },
    ]

    recommendations = [
        {
            "priority": 1,
            "category": "PRIORITÉ URGENTE",
            "title": "Angio-TDM Thoracique",
            "description": "Éliminer embolie pulmonaire (ATCD TVP + D-dimères élevés)",
            "expected_delay": "< 30 min"
        },
        {
            "priority": 2,
            "category": "Monitoring",
            "title": "Surveillance SpO2 + O2",
            "description": "SpO2 à 89%, installer O2 si < 92%",
            "expected_delay": "immédiat"
        },
        {
            "priority": 3,
            "category": "Biologie",
            "title": "Examens complémentaires",
            "description": "Gazométrie artérielle, NT-proBNP, Troponines",
            "expected_delay": "< 1h"
        },
        {
            "priority": 4,
            "category": "Préparation",
            "title": "Alerte équipe réanimation",
            "description": "Prévenir en cas de dégradation",
            "expected_delay": "standby"
        }
    ]

    chat_reply = (
        f"✅ Analyse complétée pour le patient {req.patient_id or 'N/A'}.\n\n"
        f"📊 Synthèse générée par l'Agent Synthétiseur\n"
        f"🧠 {len(differentials)} diagnostics différentiels identifiés par l'Agent Expert\n"
        f"⚠️ {len(alerts)} alertes critiques détectées par l'Agent Critique\n"
        f"💡 {len(recommendations)} recommandations immédiates formulées\n\n"
        f"Consultation complète disponible dans les panels."
    )

    # Calcul du temps de traitement
    processing_time = int((time.time() - start_time) * 1000)
    confidence = round(random.uniform(0.82, 0.95), 2)

    return AnalyzeResponse(
        analysis_id=analysis_id,
        confidence=confidence,
        processing_time_ms=processing_time,
        patient_summary=patient_summary,
        differentials=differentials,
        alerts=alerts,
        recommendations=recommendations,
        chat_reply=chat_reply,
    )

