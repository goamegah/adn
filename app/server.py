import os
import json
import uuid

import google.auth
from fastapi import FastAPI, Body, HTTPException
from fastapi.middleware.cors import CORSMiddleware
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

# AGENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AGENT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "agents")
print(f"Agent directory: {AGENT_DIR}")
session_service_uri = None

# Create Google ADK app
app: FastAPI = get_fast_api_app(
    agents_dir=AGENT_DIR,
    web=True,
    artifact_service_uri=bucket_name,
    allow_origins=allow_origins,
    session_service_uri=session_service_uri,
)
app.title = "Clinical Agent API"
app.description = "API for interacting with the Clinical Agent (Google ADK + Custom Endpoints)."

# CORS CONFIGURATION
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# CLOUD RUN CONFIGURATION (optional for calling other services)
EXTERNAL_SERVICE_URL = os.getenv("EXTERNAL_SERVICE_URL")  # Optional
APP_NAME = os.getenv("APP_NAME", "clinical_agent")


# UTILITIES
def ensure_session_exists_internal(app_name: str, user_id: str, session_id: str):
    """
    Use TestClient to verify/create a session internally.
    """
    from fastapi.testclient import TestClient
    
    client = TestClient(app)
    
    # Check if session exists
    response = client.get(f"/apps/{app_name}/users/{user_id}/sessions/{session_id}")
    
    if response.status_code == 200:
        return response.json()
    
    # Create session if it doesn't exist
    print(f"Creating session {session_id}...")
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
            detail=f"Session creation failed: {create_response.text[:500]}"
        )
    
    return create_response.json()


# CUSTOM ENDPOINTS

@app.post("/start_session")
async def start_session(req: StartSessionRequest = Body(...)):
    """
    Create a session for a given user.
    Simplified wrapper around Google ADK endpoint.
    """
    user_id = req.user_id
    session_id = f"session_{uuid.uuid4().hex[:8]}"
    app_name = APP_NAME

    print(f"Creating session {session_id} for {user_id}...")

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
                detail=f"Error: {response.text[:500]}"
            )

        data = response.json()

        logger.log_struct({
            "event": "session_created",
            "user_id": user_id,
            "session_id": data.get("id", session_id)
        }, severity="INFO")

        return {
            "success": True,
            "message": "Session created successfully",
            "user_id": user_id,
            "session_id": data.get("id", session_id),
            "created_at": data.get("createdTime"),
            "state": data.get("state", {})
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in start_session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@app.post("/send_message")
async def send_message(req: SendMessageRequest = Body(...)):
    """
    Send a message to the agent and return the response.
    """
    user_id = req.user_id or "user_backend"
    session_id = req.session_id or "session_api"
    app_name = APP_NAME

    print(f"Message from {user_id}/{session_id}: {req.query}")

    try:
        from fastapi.testclient import TestClient
        client = TestClient(app)
        
        # Ensure session exists
        ensure_session_exists_internal(app_name, user_id, session_id)

        # Send message via /run_sse endpoint
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
                detail=f"Agent error: {response.text[:500]}"
            )

        # Parse SSE response
        events = []
        for line in response.text.split('\n'):
            if line.startswith('data: '):
                try:
                    data_str = line[6:]  # Remove "data: "
                    event_json = json.loads(data_str)
                    events.append(event_json)
                except json.JSONDecodeError:
                    continue

        if not events:
            raise HTTPException(
                status_code=500,
                detail="No SSE events received"
            )

        print(f"{len(events)} events received")

        # Extract text from response
        agent_response = None
        for event in reversed(events):
            if "content" in event and "parts" in event["content"]:
                for part in event["content"]["parts"]:
                    if "text" in part:
                        agent_response = part["text"]
                        break
                if agent_response:
                    break
        
        # Clean the response
        if agent_response:
            import re
            agent_response = re.sub(r'\x00', '', agent_response)  # Null bytes
            agent_response = re.sub(r'\x1b\[[0-9;]*m', '', agent_response)  # ANSI codes
            agent_response = agent_response.strip()

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
        print(f"Error in send_message: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@app.post("/get_state")
async def get_state(req: GetStateRequest = Body(...)):
    """
    Retrieve the complete session state.
    """
    user_id = req.user_id or "user_backend"
    session_id = req.session_id or "session_api"
    app_name = APP_NAME

    print(f"Retrieving state for {user_id}/{session_id}...")

    try:
        from fastapi.testclient import TestClient
        client = TestClient(app)
        
        response = client.get(
            f"/apps/{app_name}/users/{user_id}/sessions/{session_id}"
        )

        if response.status_code == 404:
            # Create session if it doesn't exist
            print(f"Session not found, creating...")
            response = client.post(
                f"/apps/{app_name}/users/{user_id}/sessions",
                json={"session_id": session_id}
            )

        if response.status_code >= 400:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Error: {response.text[:500]}"
            )

        data = response.json()

        print(f"State retrieved: {len(str(data))} characters")

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
        print(f"Error in get_state: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@app.post("/get_agent_outputs")
async def get_agent_outputs(req: GetStateRequest = Body(...)):
    """
    Retrieve specific clinical agent outputs from state.
    """
    user_id = req.user_id or "user_backend"
    session_id = req.session_id or "session_api"
    app_name = APP_NAME

    print(f"Retrieving agent outputs for {user_id}/{session_id}...")

    try:
        from fastapi.testclient import TestClient
        client = TestClient(app)
        
        response = client.get(
            f"/apps/{app_name}/users/{user_id}/sessions/{session_id}"
        )

        if response.status_code == 404:
            raise HTTPException(status_code=404, detail="Session not found")

        if response.status_code >= 400:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Error: {response.text[:500]}"
            )

        data = response.json()
        state = data.get("state", {})

        # Extract agent outputs
        agent_outputs = {
            "donnees_patient": state.get("donnees_patient"),
            "synthese_clinique": state.get("synthese_clinique"),
            "validation_expert": state.get("validation_expert"),
        }

        # Count available outputs
        available_outputs = [k for k, v in agent_outputs.items() if v is not None]

        print(f"Outputs: {', '.join(available_outputs) if available_outputs else 'None'}")

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
        print(f"Error in get_agent_outputs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


# DEBUG ENDPOINTS

@app.get("/health")
async def health_check():
    """Check service health."""
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


# FEEDBACK ENDPOINT
@app.post("/feedback")
def collect_feedback(feedback: Feedback) -> dict[str, str]:
    """Collect and log feedback."""
    logger.log_struct(feedback.model_dump(), severity="INFO")
    return {"status": "success"}


# INCLUDE ORCHESTRATOR ROUTES
app.include_router(orchestrator_routes.router)


# MAIN
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
