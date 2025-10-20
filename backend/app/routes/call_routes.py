# backend/app/routes/call_routes.py
import threading
import uuid
import queue
import sounddevice as sd
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from google.cloud import speech
from google.oauth2 import service_account
import sys
import os
import time

router = APIRouter(prefix="/call", tags=["call"])

active_sessions = {}

RATE = 16000
CHUNK = int(RATE / 10)
CREDENTIALS_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "/home/bao/adn/key.json")

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

def analyze_transcript(session_data, new_text, is_interim=False):
    """Analyse rapide avec détection d'alertes"""
    try:
        text_lower = new_text.lower().strip()
        
        # Éviter doublons
        if text_lower in session_data.analyzed_texts:
            return
        
        session_data.analyzed_texts.add(text_lower)
        
        # Symptômes critiques
        critical = ["douleur thoracique", "difficulte a respirer", "perte de connaissance", "hemorragie", "respire pas"]
        for symptom in critical:
            if symptom in text_lower:
                session_data.alerts.append({
                    "type": "critique",
                    "symptom": symptom,
                    "text": new_text,
                    "message": f"⚠️ SYMPTÔME CRITIQUE: '{symptom}' détecté",
                    "timestamp": time.time()
                })
                print(f"🚨 CRITIQUE: {symptom}")
                return
        
        # Mots-clés urgents
        urgent = ["saigne", "inconscient", "accident", "tombe", "mal au coeur", "douleur"]
        for keyword in urgent:
            if keyword in text_lower:
                session_data.alerts.append({
                    "type": "urgence",
                    "keyword": keyword,
                    "text": new_text,
                    "message": f"🚨 URGENCE: '{keyword}' détecté",
                    "timestamp": time.time()
                })
                print(f"🚨 URGENCE: {keyword}")
                return
        
        # Analyse simple (phrases finales seulement)
        if not is_interim:
            symptoms = ["fievre", "mal", "toux", "vomit", "fatigue"]
            if any(s in text_lower for s in symptoms):
                session_data.analysis.append(f"ℹ️ Symptôme: {new_text}")
            else:
                session_data.analysis.append(f"ℹ️ Info: {new_text}")
    except Exception as e:
        print(f"Erreur analyse: {e}")

def transcription_thread(session_id, session_data):
    """Thread de transcription optimisé"""
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
                    
                    # Analyse asynchrone
                    threading.Thread(
                        target=analyze_transcript,
                        args=(session_data, transcript_text, False),
                        daemon=True
                    ).start()
                else:
                    # Mise à jour rapide
                    if current_time - session_data.last_update >= 0.5:
                        session_data.current_text = transcript_text
                        session_data.last_update = current_time
                        
                        # Analyse asynchrone si texte assez long
                        if len(transcript_text) > 5:
                            threading.Thread(
                                target=analyze_transcript,
                                args=(session_data, transcript_text, True),
                                daemon=True
                            ).start()
                    
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"🛑 Session {session_id} terminée")

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
        "caller": {
            "firstName": request.firstName,
            "lastName": request.lastName,
            "phone": request.phone
        },
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
    
    return {
        "session_id": session_id,
        "status": "stopped",
        "final_transcript": session_data.transcript,
        "final_analysis": session_data.analysis,
        "final_alerts": session_data.alerts
    }