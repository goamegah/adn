import threading
import uuid
import queue
import sounddevice as sd
from fastapi import APIRouter, HTTPException, FastAPI
from pydantic import BaseModel
from google.cloud import speech
from google.oauth2 import service_account
import sys
import os
import time
import json
from speech_to_text_agent.agent import root_agent  # importe ton agent défini dans agent.py

# ============================================================
# 📞 ROUTEUR API — importable depuis backend.main
# ============================================================

router = APIRouter(prefix="/call", tags=["call"])

# Dictionnaire pour stocker les sessions actives
active_sessions = {}

# Configuration audio
RATE = 16000
CHUNK = int(RATE / 10)
CREDENTIALS_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "/home/bao/adn/key.json")

# ============================================================
# 📦 MODELES DE DONNÉES
# ============================================================

class StartCallRequest(BaseModel):
    firstName: str
    lastName: str
    phone: str


class SessionData:
    def __init__(self):
        self.transcript = []
        self.current_text = ""
        self.analysis = []
        self.alerts = []
        self.stop_event = threading.Event()
        self.audio_queue = queue.Queue()
        self.last_update = 0
        self.analyzed_texts = set()
        self.call_type = None
        self.decision_tree = None
        self.full_transcript = ""


# ============================================================
# 🎙️ AUDIO & ANALYSE
# ============================================================

def audio_callback(indata, frames, time_info, status, session_data):
    if status:
        print(status, file=sys.stderr)
    session_data.audio_queue.put(bytes(indata))


def audio_generator(session_data):
    while not session_data.stop_event.is_set():
        data = [session_data.audio_queue.get()]
        while not session_data.audio_queue.empty():
            data.append(session_data.audio_queue.get())
        yield b"".join(data)


def analyze_with_agent(session_data, new_text, is_interim=False):
    """Analyse textuelle via root_agent"""
    try:
        text_lower = new_text.lower().strip()

        if not is_interim and text_lower in session_data.analyzed_texts:
            return

        if not is_interim:
            session_data.analyzed_texts.add(text_lower)
            session_data.full_transcript += " " + new_text

        # Détection rapide de mots critiques
        critical_keywords = {
            "arrêt cardiaque": ["ne respire pas", "inconscient", "pas de pouls"],
            "hémorragie": ["saigne beaucoup", "perd du sang"],
            "détresse respiratoire": ["ne peut pas respirer", "étouffe"],
            "intoxication": ["a pris des médicaments", "surdose"],
        }

        for category, keywords in critical_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                session_data.alerts.append({
                    "type": "critique",
                    "category": category,
                    "text": new_text,
                    "message": f"🚨 ALERTE CRITIQUE: {category}",
                    "timestamp": time.time()
                })
                print(f"🚨 CRITIQUE: {category}")

        # Analyse complète seulement pour phrases finales
        if not is_interim and len(session_data.full_transcript.split()) >= 10:
            prompt = f"""Transcription d'appel d'urgence :
{session_data.full_transcript}

Analyse :
1. Type d'urgence probable
2. Informations clés
3. Prochaines questions à poser
4. Éléments critiques éventuels"""

            response = root_agent.generate_content(prompt)

            if response and response.text:
                agent_analysis = {
                    "type": "agent_analysis",
                    "content": response.text,
                    "timestamp": time.time()
                }
                session_data.analysis.append(agent_analysis)
                print(f"🤖 Agent: {response.text[:80]}...")

    except Exception as e:
        print(f"❌ Erreur analyse: {e}")


def transcription_thread(session_id, session_data):
    """Thread principal de transcription audio"""
    try:
        credentials = service_account.Credentials.from_service_account_file(CREDENTIALS_PATH)
        client = speech.SpeechClient(credentials=credentials)

        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=RATE,
            language_code="fr-FR",
            enable_automatic_punctuation=True,
        )

        streaming_config = speech.StreamingRecognitionConfig(
            config=config, interim_results=True
        )

        def callback(indata, frames, time_info, status):
            audio_callback(indata, frames, time_info, status, session_data)

        with sd.RawInputStream(
            samplerate=RATE,
            blocksize=CHUNK,
            dtype="int16",
            channels=1,
            callback=callback,
        ):
            print(f"🎤 Session {session_id} démarrée")

            requests = (
                speech.StreamingRecognizeRequest(audio_content=chunk)
                for chunk in audio_generator(session_data)
            )

            responses = client.streaming_recognize(streaming_config, requests)

            for response in responses:
                if session_data.stop_event.is_set():
                    break
                if not response.results:
                    continue

                result = response.results[0]
                transcript_text = result.alternatives[0].transcript
                current_time = time.time()

                if result.is_final:
                    session_data.transcript.append(transcript_text)
                    session_data.current_text = ""
                    print(f"✅ {transcript_text}")
                    threading.Thread(
                        target=analyze_with_agent,
                        args=(session_data, transcript_text, False),
                        daemon=True
                    ).start()
                else:
                    if current_time - session_data.last_update >= 0.5:
                        session_data.current_text = transcript_text
                        session_data.last_update = current_time
    except Exception as e:
        print(f"❌ Erreur transcription: {e}")

    print(f"🛑 Session {session_id} terminée")


# ============================================================
# 🚀 ROUTES FASTAPI
# ============================================================

@router.post("/start")
async def start_call(request: StartCallRequest):
    session_id = str(uuid.uuid4())
    session_data = SessionData()
    active_sessions[session_id] = session_data

    thread = threading.Thread(
        target=transcription_thread,
        args=(session_id, session_data),
        daemon=True
    )
    thread.start()

    return {
        "session_id": session_id,
        "caller": request.dict(),
        "status": "recording"
    }


@router.get("/status/{session_id}")
async def get_call_status(session_id: str):
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session non trouvée")

    session_data = active_sessions[session_id]
    return {
        "session_id": session_id,
        "transcript": session_data.transcript,
        "current_text": session_data.current_text,
        "analysis": session_data.analysis,
        "alerts": session_data.alerts,
        "is_active": not session_data.stop_event.is_set()
    }


@router.post("/stop/{session_id}")
async def stop_call(session_id: str):
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session non trouvée")

    session_data = active_sessions[session_id]
    session_data.stop_event.set()

    return {"session_id": session_id, "status": "stopped"}


# ============================================================
# 🧩 MODE STANDALONE (pour uvicorn routes_arm:app)
# ============================================================

app = FastAPI(title="Speech-to-Text Agent")
app.include_router(router)
