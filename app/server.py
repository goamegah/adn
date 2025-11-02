import os
import json
import uuid

import google.auth
from fastapi import FastAPI, Body, HTTPException
from google.adk.cli.fast_api import get_fast_api_app
from google.cloud import logging as google_cloud_logging
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider, export

from app.utils.gcs import create_bucket_if_not_exists
from app.utils.tracing import CloudTraceLoggingSpanExporter
from app.utils.typing import Feedback, StartSessionRequest, SendMessageRequest, GetStateRequest
from app.routes import orchestrator_routes

_, project_id = google.auth.default()
logging_client = google_cloud_logging.Client()
logger = logging_client.logger(__name__)
allow_origins = (
    os.getenv("ALLOW_ORIGINS", "").split(",") if os.getenv("ALLOW_ORIGINS") else None
)

bucket_name = f"gs://{project_id}-adn-app-logs"
create_bucket_if_not_exists(
    bucket_name=bucket_name, project=project_id, location="europe-west1"
)

provider = TracerProvider()
processor = export.BatchSpanProcessor(CloudTraceLoggingSpanExporter())
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)

AGENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
session_service_uri = None

# ✅ Créer l'app Google ADK
app: FastAPI = get_fast_api_app(
    agents_dir=AGENT_DIR,
    web=True,
    artifact_service_uri=bucket_name,
    allow_origins=allow_origins,
    session_service_uri=session_service_uri,
)
app.title = "Clinical Agent API"
app.description = "API for interacting with the Clinical Agent (Google ADK + Custom Endpoints)."

# === CONFIGURATION POUR CLOUD RUN (si besoin d'appeler un autre service) ===
EXTERNAL_SERVICE_URL = os.getenv("EXTERNAL_SERVICE_URL")  # Optionnel
APP_NAME = os.getenv("APP_NAME", "clinical_agent")


# === UTILITAIRES ===
def ensure_session_exists_internal(app_name: str, user_id: str, session_id: str):
    """
    Utilise TestClient pour vérifier/créer une session en interne.
    """
    from fastapi.testclient import TestClient
    
    client = TestClient(app)
    
    # Vérifier si la session existe
    response = client.get(f"/apps/{app_name}/users/{user_id}/sessions/{session_id}")
    
    if response.status_code == 200:
        return response.json()
    
    # Créer la session si elle n'existe pas
    print(f"⚙️ Création de la session {session_id}...")
    create_response = client.post(
        f"/apps/{app_name}/users/{user_id}/sessions",
        json={
            "session_id": session_id,
            "state": {
                "preferred_language": "French",
                "visit_count": 1
            }
        }
    )
    
    if create_response.status_code >= 400:
        raise HTTPException(
            status_code=create_response.status_code,
            detail=f"Échec création session: {create_response.text[:500]}"
        )
    
    return create_response.json()


# === ENDPOINTS PERSONNALISÉS ===

@app.post("/start_session")
async def start_session(req: StartSessionRequest = Body(...)):
    """
    Crée une session pour un utilisateur donné.
    Wrapper simplifié autour de l'endpoint Google ADK.
    """
    user_id = req.user_id
    session_id = f"session_{uuid.uuid4().hex[:8]}"
    app_name = APP_NAME

    print(f"🚀 Création session {session_id} pour {user_id}...")

    try:
        from fastapi.testclient import TestClient
        client = TestClient(app)
        
        initial_state = req.initial_state or {
            "session_id": session_id,
            "state": {
                "preferred_language": "French",
                "visit_count": 1
            }
        }
        
        response = client.post(
            f"/apps/{app_name}/users/{user_id}/sessions",
            json=initial_state
        )

        if response.status_code >= 400:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Erreur: {response.text[:500]}"
            )

        data = response.json()

        logger.log_struct({
            "event": "session_created",
            "user_id": user_id,
            "session_id": data.get("id", session_id)
        }, severity="INFO")

        return {
            "success": True,
            "message": "Session créée avec succès ✅",
            "user_id": user_id,
            "session_id": data.get("id", session_id),
            "created_at": data.get("createdTime"),
            "state": data.get("state", {})
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Erreur start_session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")


@app.post("/send_message")
async def send_message(req: SendMessageRequest = Body(...)):
    """
    Envoie un message à l'agent et retourne la réponse.
    """
    user_id = req.user_id or "user_backend"
    session_id = req.session_id or "session_api"
    app_name = APP_NAME

    print(f"💬 Message de {user_id}/{session_id}: {req.query}")

    try:
        from fastapi.testclient import TestClient
        client = TestClient(app)
        
        # S'assurer que la session existe
        ensure_session_exists_internal(app_name, user_id, session_id)

        # Envoyer le message via l'endpoint /run_sse
        payload = {
            "app_name": app_name,
            "user_id": user_id,
            "session_id": session_id,
            "new_message": {
                "role": "user",
                "parts": [{"text": req.query}]
            },
            "streaming": False,
        }

        response = client.post("/run_sse", json=payload)

        if response.status_code >= 400:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Erreur agent: {response.text[:500]}"
            )

        # Parser la réponse SSE
        events = []
        for line in response.text.split('\n'):
            if line.startswith('data: '):
                try:
                    data_str = line[6:]  # Enlever "data: "
                    event_json = json.loads(data_str)
                    events.append(event_json)
                except json.JSONDecodeError:
                    continue

        if not events:
            raise HTTPException(
                status_code=500,
                detail="Aucun événement SSE reçu"
            )

        print(f"✅ {len(events)} événements reçus")

        # Extraire le texte de la réponse
        agent_response = None
        for event in reversed(events):
            if "content" in event and "parts" in event["content"]:
                for part in event["content"]["parts"]:
                    if "text" in part:
                        agent_response = part["text"]
                        break
                if agent_response:
                    break

        logger.log_struct({
            "event": "message_sent",
            "user_id": user_id,
            "session_id": session_id,
            "query": req.query,
            "events_count": len(events)
        }, severity="INFO")

        return {
            "success": True,
            "response": agent_response,
            "events_count": len(events),
            "session_id": session_id,
            "user_id": user_id,
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Erreur send_message: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")


@app.post("/get_state")
async def get_state(req: GetStateRequest = Body(...)):
    """
    Récupère l'état complet de la session.
    """
    user_id = req.user_id or "user_backend"
    session_id = req.session_id or "session_api"
    app_name = APP_NAME

    print(f"📊 Récupération état {user_id}/{session_id}...")

    try:
        from fastapi.testclient import TestClient
        client = TestClient(app)
        
        response = client.get(
            f"/apps/{app_name}/users/{user_id}/sessions/{session_id}"
        )

        if response.status_code == 404:
            # Créer la session si elle n'existe pas
            print(f"Session non trouvée, création...")
            response = client.post(
                f"/apps/{app_name}/users/{user_id}/sessions",
                json={"session_id": session_id}
            )

        if response.status_code >= 400:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Erreur: {response.text[:500]}"
            )

        data = response.json()

        print(f"✅ État récupéré: {len(str(data))} caractères")

        logger.log_struct({
            "event": "get_state",
            "user_id": user_id,
            "session_id": session_id
        }, severity="INFO")

        return {
            "success": True,
            "session_id": data.get("id", session_id),
            "user_id": data.get("userId", user_id),
            "state": data.get("state", {}),
            "events_count": len(data.get("events", [])),
            "created_at": data.get("createdTime"),
            "last_update": data.get("lastUpdateTime"),
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Erreur get_state: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")


@app.post("/get_agent_outputs")
async def get_agent_outputs(req: GetStateRequest = Body(...)):
    """
    Récupère les outputs spécifiques des agents cliniques depuis le state.
    """
    user_id = req.user_id or "user_backend"
    session_id = req.session_id or "session_api"
    app_name = APP_NAME

    print(f"🧠 Récupération outputs agents {user_id}/{session_id}...")

    try:
        from fastapi.testclient import TestClient
        client = TestClient(app)
        
        response = client.get(
            f"/apps/{app_name}/users/{user_id}/sessions/{session_id}"
        )

        if response.status_code == 404:
            raise HTTPException(status_code=404, detail="Session non trouvée")

        if response.status_code >= 400:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Erreur: {response.text[:500]}"
            )

        data = response.json()
        state = data.get("state", {})

        # Extraire les outputs des agents
        agent_outputs = {
            "donnees_patient": state.get("donnees_patient"),
            "synthese_clinique": state.get("synthese_clinique"),
            "validation_expert": state.get("validation_expert"),
        }

        # Compter les outputs disponibles
        available_outputs = [k for k, v in agent_outputs.items() if v is not None]

        print(f"✅ Outputs: {', '.join(available_outputs) if available_outputs else 'Aucun'}")

        logger.log_struct({
            "event": "get_agent_outputs",
            "user_id": user_id,
            "session_id": session_id,
            "available_outputs": available_outputs
        }, severity="INFO")

        return {
            "success": True,
            "session_id": data.get("id", session_id),
            "user_id": data.get("userId", user_id),
            "agent_outputs": agent_outputs,
            "available_outputs": available_outputs,
            "last_update": data.get("lastUpdateTime"),
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Erreur get_agent_outputs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")


# === ENDPOINTS DE DEBUG ===

@app.get("/health")
async def health_check():
    """Vérifie la santé du service."""
    return {
        "status": "ok",
        "service": "Clinical Agent API",
        "app_name": APP_NAME,
        "endpoints": {
            "adk": "Google ADK endpoints (see /docs)",
            "custom": [
                "POST /start_session",
                "POST /send_message", 
                "POST /get_state",
                "POST /get_agent_outputs"
            ]
        }
    }


# === ENDPOINT FEEDBACK (déjà existant) ===
@app.post("/feedback")
def collect_feedback(feedback: Feedback) -> dict[str, str]:
    """Collect and log feedback."""
    logger.log_struct(feedback.model_dump(), severity="INFO")
    return {"status": "success"}


# === INCLURE LES ROUTES ORCHESTRATOR ===
app.include_router(orchestrator_routes.router)


# === MAIN ===
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)