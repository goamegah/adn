/* components/VoiceRecorder.jsx - Enregistrement vocal avec WebSocket */
'use client'
import { useState, useRef, useEffect } from 'react'
import { Mic, MicOff, Volume2, Loader2 } from './icons'

export default function VoiceRecorder({ onTranscription }) {
  const [isRecording, setIsRecording] = useState(false)
  const [isPlaying, setIsPlaying] = useState(false)
  const [isConnected, setIsConnected] = useState(false)
  const [error, setError] = useState(null)
  const [transcription, setTranscription] = useState('')
  
  const wsRef = useRef(null)
  const mediaRecorderRef = useRef(null)
  const audioContextRef = useRef(null)
  const audioQueueRef = useRef([])

  // Connexion WebSocket au backend
  useEffect(() => {
    connectWebSocket()
    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [])

  const connectWebSocket = () => {
    try {
      // Connexion au backend proxy
      const wsUrl = process.env.NEXT_PUBLIC_BACKEND_WS_URL || 'ws://localhost:8000/api/voice/stream'
      console.log('🔌 Connexion au backend vocal:', wsUrl)
      
      const ws = new WebSocket(wsUrl)
      
      ws.onopen = () => {
        console.log('✅ WebSocket connecté')
        setIsConnected(true)
        setError(null)
      }
      
      ws.onmessage = async (event) => {
        try {
          const data = JSON.parse(event.data)
          
          if (data.type === 'audio') {
            // Recevoir et jouer l'audio de réponse
            await playAudioChunk(data.data)
          } else if (data.type === 'text') {
            // Recevoir la transcription
            console.log('📝 Transcription:', data.data)
            setTranscription(data.data)
            if (onTranscription) {
              onTranscription(data.data)
            }
          } else if (data.type === 'error') {
            console.error('❌ Erreur serveur:', data.message)
            setError(data.message)
          }
        } catch (err) {
          console.error('❌ Erreur traitement message:', err)
        }
      }
      
      ws.onerror = (err) => {
        console.error('❌ Erreur WebSocket:', err)
        setError('Erreur de connexion au serveur vocal')
        setIsConnected(false)
      }
      
      ws.onclose = () => {
        console.log('🔌 WebSocket fermé')
        setIsConnected(false)
        // Reconnexion automatique après 3s
        setTimeout(() => {
          if (!wsRef.current || wsRef.current.readyState === WebSocket.CLOSED) {
            connectWebSocket()
          }
        }, 3000)
      }
      
      wsRef.current = ws
    } catch (err) {
      console.error('❌ Erreur création WebSocket:', err)
      setError('Impossible de se connecter au serveur vocal')
    }
  }

  const startRecording = async () => {
    if (!isConnected) {
      setError('Non connecté au serveur vocal')
      return
    }

    try {
      // Demander l'accès au microphone
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          sampleRate: 16000,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
        } 
      })
      
      // Créer le MediaRecorder
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      })
      
      mediaRecorder.ondataavailable = async (event) => {
        if (event.data.size > 0 && wsRef.current?.readyState === WebSocket.OPEN) {
          // Convertir en base64 et envoyer
          const reader = new FileReader()
          reader.onloadend = () => {
            const base64 = reader.result.split(',')[1]
            wsRef.current.send(JSON.stringify({
              type: 'audio',
              data: base64
            }))
          }
          reader.readAsDataURL(event.data)
        }
      }
      
      // Envoyer des chunks toutes les 100ms
      mediaRecorder.start(100)
      mediaRecorderRef.current = mediaRecorder
      
      setIsRecording(true)
      setError(null)
      console.log('🎤 Enregistrement démarré')
    } catch (err) {
      console.error('❌ Erreur démarrage enregistrement:', err)
      setError('Impossible d\'accéder au microphone')
    }
  }

  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop()
      mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop())
      setIsRecording(false)
      console.log('⏹️ Enregistrement arrêté')
    }
  }

  const playAudioChunk = async (base64Audio) => {
    try {
      // Décoder le base64 en ArrayBuffer
      const binaryString = atob(base64Audio)
      const bytes = new Uint8Array(binaryString.length)
      for (let i = 0; i < binaryString.length; i++) {
        bytes[i] = binaryString.charCodeAt(i)
      }
      
      // Créer AudioContext si nécessaire
      if (!audioContextRef.current) {
        audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)()
      }
      
      const audioContext = audioContextRef.current
      
      // Décoder l'audio
      const audioBuffer = await audioContext.decodeAudioData(bytes.buffer)
      
      // Créer une source et la jouer
      const source = audioContext.createBufferSource()
      source.buffer = audioBuffer
      source.connect(audioContext.destination)
      
      setIsPlaying(true)
      source.start(0)
      
      source.onended = () => {
        setIsPlaying(false)
      }
    } catch (err) {
      console.error('❌ Erreur lecture audio:', err)
    }
  }

  return (
    <div className="flex flex-col gap-3">
      {/* Status Connection */}
      <div className="flex items-center gap-2 text-xs">
        <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-400' : 'bg-red-400'} animate-pulse`}></div>
        <span className="text-slate-400">
          {isConnected ? 'Connecté au serveur vocal' : 'Déconnecté'}
        </span>
      </div>

      {/* Recording Button */}
      <button
        onClick={isRecording ? stopRecording : startRecording}
        disabled={!isConnected}
        className={`flex items-center justify-center gap-3 w-full py-4 rounded-xl font-semibold transition-all ${
          isRecording
            ? 'bg-red-600 hover:bg-red-700 text-white animate-pulse'
            : 'bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white'
        } disabled:opacity-50 disabled:cursor-not-allowed`}
      >
        {isRecording ? (
          <>
            <MicOff className="w-5 h-5" />
            Arrêter l'enregistrement
          </>
        ) : (
          <>
            <Mic className="w-5 h-5" />
            Commencer à parler
          </>
        )}
      </button>

      {/* Playing Indicator */}
      {isPlaying && (
        <div className="flex items-center gap-2 text-sm text-blue-400 bg-blue-500/10 rounded-lg p-3">
          <Volume2 className="w-4 h-4 animate-pulse" />
          <span>Lecture de la réponse audio...</span>
        </div>
      )}

      {/* Transcription Display */}
      {transcription && (
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-3">
          <p className="text-xs text-slate-400 mb-1">Transcription :</p>
          <p className="text-sm text-white">{transcription}</p>
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="bg-red-500/10 border border-red-500/50 rounded-lg p-3 text-sm text-red-300">
          {error}
        </div>
      )}
    </div>
  )
}