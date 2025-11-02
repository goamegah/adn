from fastapi import FastAPI, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import json
import os
from dotenv import load_dotenv
import uuid

from backend.routes_arm import router as speech_router


load_dotenv()

app = FastAPI(title="Clinical Agent API Gateway")

# === CONFIGURATION CORS ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(speech_router)


# === CONFIGURATION ===
APP_URL = os.getenv("APP_URL", "https://arm-agent-service-329720391631.us-east4.run.app")
APP_NAME = os.getenv("APP_NAME", "arm-agent-app")


# Headers pour Cloud Run
headers = {"Content-Type": "application/json"}
TOKEN = os.getenv("TOKEN")
if TOKEN:
    headers["Authorization"] = f"Bearer {TOKEN}"



# === SCHEMAS ===
class StartSessionRequest(BaseModel):
    user_id: str

class SendMessageRequest(BaseModel):
    user_id: str | None = None
    session_id: str | None = None
    query: str

class GetStateRequest(BaseModel):
    user_id: str | None = None
    session_id: str | None = None


# === ROUTES ===

@app.post("/start_session")
def start_session(req: StartSessionRequest = Body(...)):
    """
    Crée une session Cloud Run pour un utilisateur donné.
    """
    user_id = req.user_id
    session_id = f"session_{uuid.uuid4().hex[:8]}"

    payload = {"preferred_language": "French", "visit_count": 1}

    print(f"🚀 Création session {session_id} pour {user_id} sur {APP_NAME}...")

    response = requests.post(
        f"{APP_URL}/apps/{APP_NAME}/users/{user_id}/sessions/{session_id}",
        headers=headers,
        json=payload,
    )

    try:
        data = response.json()
    except Exception:
        return {"error": response.text}

    if "id" in data:
        return {
            "message": "Session créée avec succès ✅",
            "user_id": user_id,
            "session_id": session_id,
            "agent_response": data,
        }
    else:
        return {"error": "Échec de création de session", "response": data}


@app.post("/send_message")
def send_message(req: SendMessageRequest = Body(...)):
    """
    Envoie un message à l'agent clinique et retourne uniquement l'output texte.
    """
    user_id = req.user_id or "user_backend"
    session_id = req.session_id or "session_api"

    # Vérifie ou crée la session si besoin
    print(f"📡 Vérification session {session_id}...")
    session_check = requests.get(f"{APP_URL}/apps/{APP_NAME}/users/{user_id}/sessions", headers=headers)
    if session_check.status_code != 200 or session_id not in session_check.text:
        # créer la session si absente
        print(f"⚙️ Session {session_id} absente — création...")
        start_payload = {"preferred_language": "French", "visit_count": 1}
        _ = requests.post(
            f"{APP_URL}/apps/{APP_NAME}/users/{user_id}/sessions/{session_id}",
            headers=headers,
            json=start_payload,
        )

    # Prépare la requête principale
    payload = {
        "app_name": APP_NAME,
        "user_id": user_id,
        "session_id": session_id,
        "new_message": {"role": "user", "parts": [{"text": req.query}]},
        "streaming": False,
    }

    print(f"💬 Envoi au Clinical Agent: {req.query}")
    response = requests.post(f"{APP_URL}/run_sse", headers=headers, json=payload, timeout=60)

    # Parser la réponse SSE
    response_text = response.text
    print(f"📦 Réponse brute reçue ({len(response_text)} chars)")
    
    # Extraire les événements SSE
    events = []
    for line in response_text.split('\n'):
        if line.startswith('data: '):
            try:
                data_str = line[6:]  # Enlever "data: "
                event_json = json.loads(data_str)
                events.append(event_json)
            except json.JSONDecodeError:
                continue
    
    if not events:
        return {"error": "Aucun événement SSE valide"}
    
    print(f"✅ {len(events)} événements SSE parsés")
    
    # Extraire le texte du dernier événement
    for event in reversed(events):
        if "content" in event and "parts" in event["content"]:
            for part in event["content"]["parts"]:
                if "text" in part:
                    return {"response": part["text"]}
    
    # Fallback: retourner tous les événements
    return {"output": events}


@app.post("/get_state")
def get_state(req: GetStateRequest = Body(...)):
    """
    Récupère l'état (state) de la session pour un utilisateur donné.
    """
    user_id = req.user_id or "user_backend"
    session_id = req.session_id or "session_api"

    print(f"📊 Récupération de l'état pour {user_id}/{session_id}...")

    try:
        # Récupérer la session
        response = requests.get(
            f"{APP_URL}/apps/{APP_NAME}/users/{user_id}/sessions/{session_id}",
            headers=headers,
            timeout=10
        )

        if response.status_code == 404:
            return {"error": "Session non trouvée"}
        
        if response.status_code != 200:
            return {"error": f"Erreur HTTP {response.status_code}", "details": response.text[:500]}

        data = response.json()
        
        print(f"✅ État récupéré: {len(str(data))} caractères")
        
        # Retourner l'état de la session
        return {
            "session_id": data.get("id", session_id),
            "user_id": data.get("userId", user_id),
            "state": data.get("state", {}),
            "events": data.get("events", []),
            "last_update": data.get("lastUpdateTime"),
        }

    except requests.exceptions.Timeout:
        return {"error": "Timeout lors de la récupération de l'état"}
    except Exception as e:
        print(f"❌ Erreur get_state: {str(e)}")
        return {"error": f"Erreur: {str(e)}"}


@app.post("/get_agent_outputs")
def get_agent_outputs(req: GetStateRequest = Body(...)):
    """
    Récupère les outputs des agents (collecteur, synthétiseur, expert) depuis le state.
    Extrait spécifiquement:
    - donnees_patient (collecteur_agent)
    - synthese_clinique (synthetiseur_agent)
    - validation_expert (expert_agent)
    """
    user_id = req.user_id or "user_backend"
    session_id = req.session_id or "session_api"

    print(f"🧠 Récupération des outputs agents pour {user_id}/{session_id}...")

    try:
        # Récupérer la session
        response = requests.get(
            f"{APP_URL}/apps/{APP_NAME}/users/{user_id}/sessions/{session_id}",
            headers=headers,
            timeout=10
        )

        if response.status_code == 404:
            return {"error": "Session non trouvée"}
        
        if response.status_code != 200:
            return {"error": f"Erreur HTTP {response.status_code}", "details": response.text[:500]}

        data = response.json()
        state = data.get("state", {})
        
        # Extraire les outputs des agents
        agent_outputs = {
            "donnees_patient": state.get("donnees_patient", None),
            "synthese_clinique": state.get("synthese_clinique", None),
            "validation_expert": state.get("validation_expert", None),
        }
        
        # Compter les agents qui ont produit des résultats
        available_outputs = [k for k, v in agent_outputs.items() if v is not None]
        
        print(f"✅ Outputs disponibles: {', '.join(available_outputs) if available_outputs else 'Aucun'}")
        
        return {
            "session_id": data.get("id", session_id),
            "user_id": data.get("userId", user_id),
            "agent_outputs": agent_outputs,
            "available_outputs": available_outputs,
            "last_update": data.get("lastUpdateTime"),
        }

    except requests.exceptions.Timeout:
        return {"error": "Timeout lors de la récupération des outputs"}
    except Exception as e:
        print(f"❌ Erreur get_agent_outputs: {str(e)}")
        return {"error": f"Erreur: {str(e)}"}


@app.post("/get_execution_trace")
def get_execution_trace(req: GetStateRequest = Body(...)):
    """
    Récupère la trace d'exécution complète de l'agent :
    - Historique des messages (user/agent)
    - Tool calls effectués par l'agent
    - Résultats des tools
    - Timeline d'exécution
    
    Format similaire à ADK Web pour affichage dans le frontend.
    """
    user_id = req.user_id or "user_backend"
    session_id = req.session_id or "session_api"

    print(f"🔍 Récupération trace d'exécution pour {user_id}/{session_id}...")

    try:
        # Récupérer la session complète
        response = requests.get(
            f"{APP_URL}/apps/{APP_NAME}/users/{user_id}/sessions/{session_id}",
            headers=headers,
            timeout=10
        )

        if response.status_code == 404:
            return {"error": "Session non trouvée"}
        
        if response.status_code != 200:
            return {"error": f"Erreur HTTP {response.status_code}", "details": response.text[:500]}

        data = response.json()
        
        # Extraire les events (historique d'exécution)
        events = data.get("events", [])
        state = data.get("state", {})
        
        # Parser les events pour extraire les tool calls
        execution_trace = {
            "messages": [],
            "tool_calls": [],
            "timeline": []
        }
        
        for event in events:
            event_type = event.get("type", "")
            timestamp = event.get("timestamp")
            content = event.get("content", {})
            
            # Messages utilisateur et agent
            if event_type == "user_message":
                execution_trace["messages"].append({
                    "role": "user",
                    "timestamp": timestamp,
                    "content": content.get("parts", [{}])[0].get("text", "")
                })
            
            elif event_type == "agent_message":
                execution_trace["messages"].append({
                    "role": "agent",
                    "timestamp": timestamp,
                    "content": content.get("parts", [{}])[0].get("text", "")
                })
            
            # Tool calls (function declarations)
            elif event_type == "tool_call":
                tool_name = content.get("name", "unknown")
                tool_args = content.get("args", {})
                
                execution_trace["tool_calls"].append({
                    "timestamp": timestamp,
                    "tool_name": tool_name,
                    "arguments": tool_args,
                    "status": "called"
                })
                
                execution_trace["timeline"].append({
                    "timestamp": timestamp,
                    "type": "tool_call",
                    "description": f"Appel de {tool_name}",
                    "details": tool_args
                })
            
            # Tool responses (résultats)
            elif event_type == "tool_response":
                tool_name = content.get("name", "unknown")
                tool_result = content.get("response", {})
                
                # Trouver le tool call correspondant et ajouter le résultat
                for tc in reversed(execution_trace["tool_calls"]):
                    if tc["tool_name"] == tool_name and tc["status"] == "called":
                        tc["result"] = tool_result
                        tc["status"] = "completed"
                        break
                
                execution_trace["timeline"].append({
                    "timestamp": timestamp,
                    "type": "tool_response",
                    "description": f"Résultat de {tool_name}",
                    "details": tool_result
                })
            
            # Autres events
            else:
                execution_trace["timeline"].append({
                    "timestamp": timestamp,
                    "type": event_type,
                    "description": f"Event: {event_type}",
                    "details": content
                })
        
        # Statistiques
        stats = {
            "total_messages": len(execution_trace["messages"]),
            "user_messages": len([m for m in execution_trace["messages"] if m["role"] == "user"]),
            "agent_messages": len([m for m in execution_trace["messages"] if m["role"] == "agent"]),
            "total_tool_calls": len(execution_trace["tool_calls"]),
            "completed_tool_calls": len([tc for tc in execution_trace["tool_calls"] if tc["status"] == "completed"]),
            "tool_types": list(set([tc["tool_name"] for tc in execution_trace["tool_calls"]]))
        }
        
        print(f"✅ Trace récupérée: {stats['total_tool_calls']} tool calls, {stats['total_messages']} messages")
        
        return {
            "session_id": data.get("id", session_id),
            "user_id": data.get("userId", user_id),
            "execution_trace": execution_trace,
            "statistics": stats,
            "state": state,
            "last_update": data.get("lastUpdateTime"),
        }

    except requests.exceptions.Timeout:
        return {"error": "Timeout lors de la récupération de la trace"}
    except Exception as e:
        print(f"❌ Erreur get_execution_trace: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"error": f"Erreur: {str(e)}"}



@app.get("/")
def root():
    return {"message": "Backend FastAPI connecté à ton agent clinique Cloud Run 🚀"}