# backend/app/routes/call_routes.pys
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

# Sessions actives : {session_id: {transcript, analysis, stop_event, thread}}
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
        self.transcript = []  # Liste de phrases finales
        self.current_text = ""  # Texte en cours (mis à jour toutes les secondes)
        self.analysis = []    # Liste d'analyses
        self.stop_event = threading.Event()
        self.audio_queue = queue.Queue()
        self.last_update = 0  # Timestamp du dernier update

def audio_callback(indata, frames, time, status, session_data):
    if status:
        print(status, file=sys.stderr)
    session_data.audio_queue.put(bytes(indata))

def audio_generator(session_data):
    while not session_data.stop_event.is_set():
        data = [session_data.audio_queue.get()]
        while not session_data.audio_queue.empty():
            data.append(session_data.audio_queue.get())
        yield b"".join(data)

def transcription_thread(session_id, session_data):
    """Thread qui enregistre et transcrit en continu"""
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
    
    def callback(indata, frames, time, status):
        audio_callback(indata, frames, time, status, session_data)
    
    with sd.RawInputStream(
        samplerate=RATE,
        blocksize=CHUNK,
        dtype="int16",
        channels=1,
        callback=callback,
    ):
        print(f"🎤 Enregistrement session {session_id} démarré...")
        
        requests = (
            speech.StreamingRecognizeRequest(audio_content=chunk)
            for chunk in audio_generator(session_data)
        )
        
        try:
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
                    # Phrase finalisée
                    session_data.transcript.append(transcript_text)
                    session_data.current_text = ""
                    print(f"✅ Phrase finalisée: {transcript_text}")
                    
                    # Lancer l'analyse
                    analyze_transcript(session_data, transcript_text)
                else:
                    # Texte en cours - mise à jour toutes les secondes
                    if current_time - session_data.last_update >= 1.0:
                        session_data.current_text = transcript_text
                        session_data.last_update = current_time
                        print(f"⏳ En cours (1s): {transcript_text}")
                        
                        # Ajouter au transcript toutes les secondes
                        if transcript_text and transcript_text not in session_data.transcript:
                            session_data.transcript.append(f"[en cours] {transcript_text}")
                    
        except Exception as e:
            print(f"❌ Erreur transcription: {e}")
    
    print(f"🛑 Enregistrement session {session_id} terminé")

def analyze_transcript(session_data, new_text):
    """Analyse simple avec des mots-clés (à remplacer par Gemini plus tard)"""
    analysis = ""
    
    # Détection simple de mots-clés
    urgent_keywords = ["douleur", "saigne", "inconscient", "respire pas", "accident"]
    symptoms_keywords = ["fièvre", "mal", "toux", "vomit"]
    
    text_lower = new_text.lower()
    
    if any(keyword in text_lower for keyword in urgent_keywords):
        analysis = f"🚨 URGENCE DÉTECTÉE: '{new_text}' - Évaluer immédiatement la gravité"
    elif any(keyword in text_lower for keyword in symptoms_keywords):
        analysis = f"⚠️ Symptôme identifié: '{new_text}' - Poser questions complémentaires"
    else:
        analysis = f"ℹ️ Information notée: '{new_text}'"
    
    session_data.analysis.append(analysis)
    print(f"🤖 Analyse: {analysis}")

@router.post("/start")
async def start_call(request: StartCallRequest):
    """Démarre une session d'appel avec enregistrement"""
    session_id = str(uuid.uuid4())
    
    session_data = SessionData()
    active_sessions[session_id] = session_data
    
    # Démarrer le thread de transcription
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
    """Récupère le transcript et analyses en cours"""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session non trouvée")
    
    session_data = active_sessions[session_id]
    
    return {
        "session_id": session_id,
        "transcript": session_data.transcript,
        "current_text": session_data.current_text,
        "analysis": session_data.analysis,
        "is_active": not session_data.stop_event.is_set()
    }

@router.post("/stop/{session_id}")
async def stop_call(session_id: str):
    """Arrête l'enregistrement d'une session"""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session non trouvée")
    
    session_data = active_sessions[session_id]
    session_data.stop_event.set()
    
    return {
        "session_id": session_id,
        "status": "stopped",
        "final_transcript": session_data.transcript,
        "final_analysis": session_data.analysis
    }