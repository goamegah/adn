import queue
import sys
import threading
import sounddevice as sd
from google.cloud import speech
from google.oauth2 import service_account

# Audio parameters
RATE = 16000
CHUNK = int(RATE / 10)

# Google Cloud credentials
CREDENTIALS_PATH = "/home/bao/adn/key.json"
credentials = service_account.Credentials.from_service_account_file(CREDENTIALS_PATH)
client = speech.SpeechClient(credentials=credentials)

# Audio buffer
q = queue.Queue()
stop_recording = threading.Event()

def audio_callback(indata, frames, time, status):
    """Collect audio data."""
    if status:
        print(status, file=sys.stderr)
    q.put(bytes(indata))

def audio_generator():
    """Generator yielding audio chunks until Enter is pressed."""
    with sd.RawInputStream(
        samplerate=RATE,
        blocksize=CHUNK,
        dtype="int16",
        channels=1,
        callback=audio_callback,
    ):
        print("🎤 Enregistrement... (appuie sur Entrée pour arrêter)\n")
        while not stop_recording.is_set():
            data = [q.get()]
            while not q.empty():
                data.append(q.get())
            yield b"".join(data)
    # 🔹 Une fois stop_recording activé, on signale la fin du flux
    yield None

def listen_and_transcribe():
    """Stream microphone input to Google Cloud Speech-to-Text."""
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=RATE,
        language_code="fr-FR",
        enable_automatic_punctuation=True,
    )

    streaming_config = speech.StreamingRecognitionConfig(
        config=config, interim_results=True
    )

    # Crée les requêtes à partir des chunks audio
    requests = (
        speech.StreamingRecognizeRequest(audio_content=chunk)
        for chunk in audio_generator()
        if chunk is not None
    )

    responses = client.streaming_recognize(streaming_config, requests)
    full_transcript = ""

    try:
        for response in responses:
            if not response.results:
                continue

            result = response.results[0]
            transcript = result.alternatives[0].transcript

            if not result.is_final:
                sys.stdout.write("\r" + transcript)
                sys.stdout.flush()
            else:
                print("\n✅ Phrase détectée :", transcript)
                full_transcript += transcript.strip() + " "

            if stop_recording.is_set():
                break

    except Exception as e:
        print(f"\n⚠️ Fin du streaming : {e}")

    print("\n📝 Transcription complète :")
    print(full_transcript.strip())
    return full_transcript.strip()

def wait_for_enter():
    """Stop recording when Enter is pressed."""
    input()  # Bloque jusqu’à ce qu'on appuie sur Entrée
    stop_recording.set()
    print("\n🛑 Arrêt demandé par l'utilisateur...")

if __name__ == "__main__":
    # Thread pour surveiller la touche Entrée
    stopper = threading.Thread(target=wait_for_enter, daemon=True)
    stopper.start()

    transcription = listen_and_transcribe()

    print("\n✅ Texte final enregistré :")
    print(transcription)
