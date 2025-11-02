/* components/ARMPanel.jsx - Version avec ancien design + support vocal */
'use client'
import { useState, useRef, useEffect } from 'react'
import { Phone, Mic, MicOff, Volume2, Send, User, Sparkles, AlertTriangle } from './icons'

export default function ARMPanel() {
  const [isRecording, setIsRecording] = useState(false)
  const [isConnected, setIsConnected] = useState(false)
  const [transcript, setTranscript] = useState('')
  const [suggestions, setSuggestions] = useState([])
  const [messages, setMessages] = useState([])
  const [inputMessage, setInputMessage] = useState('')
  
  const wsRef = useRef(null)
  const mediaRecorderRef = useRef(null)
  const transcriptEndRef = useRef(null)
  const messagesEndRef = useRef(null)

  // Auto-scroll
  useEffect(() => {
    transcriptEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [transcript])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Connexion WebSocket
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
      const wsUrl = process.env.NEXT_PUBLIC_BACKEND_WS_URL || 'ws://localhost:8000/api/voice/stream'
      console.log('🔌 Connexion WebSocket:', wsUrl)
      
      const ws = new WebSocket(wsUrl)
      
      ws.onopen = () => {
        console.log('✅ WebSocket connecté')
        setIsConnected(true)
      }
      
      ws.onmessage = async (event) => {
        try {
          const data = JSON.parse(event.data)
          
          if (data.type === 'text') {
            // Ajouter au transcript
            setTranscript(prev => prev + ' ' + data.data)
            
            // TODO: Analyser le texte et générer des suggestions
            // Pour l'instant, on simule des suggestions
            if (data.data.toLowerCase().includes('douleur')) {
              addSuggestion('Depuis combien de temps avez-vous cette douleur ?')
            }
            if (data.data.toLowerCase().includes('thoracique')) {
              addSuggestion('La douleur irradie-t-elle dans le bras gauche ?', 'urgent')
            }
          }
        } catch (err) {
          console.error('❌ Erreur traitement message:', err)
        }
      }
      
      ws.onerror = (err) => {
        console.error('❌ Erreur WebSocket:', err)
        setIsConnected(false)
      }
      
      ws.onclose = () => {
        console.log('🔌 WebSocket fermé')
        setIsConnected(false)
        // Reconnexion automatique
        setTimeout(() => {
          if (!wsRef.current || wsRef.current.readyState === WebSocket.CLOSED) {
            connectWebSocket()
          }
        }, 3000)
      }
      
      wsRef.current = ws
    } catch (err) {
      console.error('❌ Erreur création WebSocket:', err)
    }
  }

  const addSuggestion = (text, priority = 'normal') => {
    setSuggestions(prev => [...prev, { 
      text, 
      priority, 
      id: Date.now(),
      timestamp: new Date().toLocaleTimeString()
    }])
  }

  const startRecording = async () => {
    if (!isConnected) {
      alert('Non connecté au serveur vocal')
      return
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          sampleRate: 16000,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
        } 
      })
      
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      })
      
      mediaRecorder.ondataavailable = async (event) => {
        if (event.data.size > 0 && wsRef.current?.readyState === WebSocket.OPEN) {
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
      
      mediaRecorder.start(100)
      mediaRecorderRef.current = mediaRecorder
      setIsRecording(true)
      console.log('🎤 Enregistrement démarré')
    } catch (err) {
      console.error('❌ Erreur démarrage enregistrement:', err)
      alert('Impossible d\'accéder au microphone')
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

  const handleSendMessage = (e) => {
    e.preventDefault()
    if (!inputMessage.trim()) return

    // Ajouter le message au chat
    setMessages(prev => [...prev, {
      role: 'user',
      content: inputMessage,
      timestamp: new Date().toLocaleTimeString()
    }])

    // TODO: Envoyer au classifier agent pour analyse
    // Simuler une réponse IA
    setTimeout(() => {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Basé sur votre question, voici ce que je suggère...',
        timestamp: new Date().toLocaleTimeString()
      }])
    }, 1000)

    setInputMessage('')
  }

  const clearTranscript = () => {
    setTranscript('')
    setSuggestions([])
  }

  return (
    <div className="h-full flex flex-col bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* Header */}
      <div className="flex-shrink-0 border-b border-slate-700/50 bg-slate-900/50 backdrop-blur-sm">
        <div className="p-4">
          <div className="flex items-center justify-between">
            {/* Titre */}
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-gradient-to-br from-green-500 to-emerald-600 rounded-xl flex items-center justify-center shadow-lg">
                <Phone className="w-7 h-7 text-white" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-white">Assistant de Régulation Médicale</h2>
                <p className="text-sm text-slate-400">Transcription en temps réel & Suggestions IA</p>
              </div>
            </div>
            
            {/* Status & Controls */}
            <div className="flex items-center gap-4">
              {/* Connection Status */}
              <div className="flex items-center gap-2 px-3 py-1.5 bg-slate-800 rounded-lg">
                <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-400 animate-pulse' : 'bg-red-400'}`}></div>
                <span className="text-xs text-slate-300">
                  {isConnected ? 'Connecté' : 'Déconnecté'}
                </span>
              </div>

              {/* Record Button */}
              <button
                onClick={isRecording ? stopRecording : startRecording}
                disabled={!isConnected}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg font-semibold transition-all ${
                  isRecording
                    ? 'bg-red-600 hover:bg-red-700 text-white animate-pulse'
                    : 'bg-green-600 hover:bg-green-700 text-white'
                } disabled:opacity-50 disabled:cursor-not-allowed`}
              >
                {isRecording ? (
                  <>
                    <MicOff className="w-5 h-5" />
                    <span className="hidden sm:inline">Arrêter</span>
                  </>
                ) : (
                  <>
                    <Mic className="w-5 h-5" />
                    <span className="hidden sm:inline">Enregistrer</span>
                  </>
                )}
              </button>

              {/* Clear Button */}
              {transcript && (
                <button
                  onClick={clearTranscript}
                  className="px-3 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg text-sm text-slate-300 transition-colors"
                >
                  Effacer
                </button>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Main Content - Two Panels */}
      <div className="flex-1 flex gap-4 p-4 overflow-hidden">
        
        {/* LEFT PANEL - Transcription */}
        <div className="flex-1 flex flex-col bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700/50 overflow-hidden">
          {/* Transcript Header */}
          <div className="flex-shrink-0 px-4 py-3 border-b border-slate-700/50 bg-slate-900/30">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold text-white flex items-center gap-2">
                <Volume2 className="w-5 h-5 text-blue-400" />
                Transcription de l'Appel
              </h3>
              {isRecording && (
                <span className="text-xs text-green-400 flex items-center gap-1">
                  <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></span>
                  En cours...
                </span>
              )}
            </div>
          </div>

          {/* Transcript Content */}
          <div className="flex-1 overflow-y-auto p-4">
            {transcript ? (
              <div className="space-y-3">
                <div className="bg-slate-900/50 rounded-lg p-4 border border-slate-700/30">
                  <p className="text-slate-200 leading-relaxed whitespace-pre-wrap">
                    {transcript}
                  </p>
                </div>
                <div ref={transcriptEndRef} />
              </div>
            ) : (
              <div className="h-full flex flex-col items-center justify-center text-center px-4">
                <div className="w-16 h-16 bg-slate-700/50 rounded-full flex items-center justify-center mb-4">
                  <Mic className="w-8 h-8 text-slate-500" />
                </div>
                <p className="text-slate-400 font-medium mb-2">En attente d'enregistrement</p>
                <p className="text-sm text-slate-500 max-w-xs">
                  Cliquez sur "Enregistrer" pour commencer la transcription en temps réel
                </p>
              </div>
            )}
          </div>

          {/* Suggestions rapides si dispo */}
          {suggestions.length > 0 && (
            <div className="flex-shrink-0 border-t border-slate-700/50 bg-slate-900/30 p-3">
              <p className="text-xs text-slate-400 mb-2 font-medium">Alertes détectées :</p>
              <div className="flex flex-wrap gap-2">
                {suggestions.slice(-3).map(sugg => (
                  <div
                    key={sugg.id}
                    className={`px-3 py-1 rounded-full text-xs font-medium ${
                      sugg.priority === 'urgent'
                        ? 'bg-red-500/20 text-red-300 border border-red-500/50'
                        : 'bg-yellow-500/20 text-yellow-300 border border-yellow-500/50'
                    }`}
                  >
                    {sugg.text.substring(0, 40)}...
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* RIGHT PANEL - Suggestions & Chat */}
        <div className="w-[45%] flex flex-col bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700/50 overflow-hidden">
          {/* Chat Header */}
          <div className="flex-shrink-0 px-4 py-3 border-b border-slate-700/50 bg-slate-900/30">
            <h3 className="font-semibold text-white flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-yellow-400" />
              Suggestions en Temps Réel
            </h3>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3">
            {suggestions.length === 0 && messages.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-center px-4">
                <div className="w-16 h-16 bg-slate-700/50 rounded-full flex items-center justify-center mb-4">
                  <Sparkles className="w-8 h-8 text-slate-500" />
                </div>
                <p className="text-slate-400 font-medium mb-2">Suggestions IA</p>
                <p className="text-sm text-slate-500 max-w-xs">
                  Les questions suggérées apparaîtront ici en fonction de la transcription
                </p>
              </div>
            ) : (
              <>
                {/* Suggestions automatiques */}
                {suggestions.map(sugg => (
                  <div
                    key={sugg.id}
                    className={`p-3 rounded-lg border-l-4 ${
                      sugg.priority === 'urgent'
                        ? 'bg-red-500/10 border-red-500'
                        : 'bg-yellow-500/10 border-yellow-500'
                    }`}
                  >
                    <div className="flex items-start gap-2">
                      <AlertTriangle className={`w-5 h-5 flex-shrink-0 mt-0.5 ${
                        sugg.priority === 'urgent' ? 'text-red-400' : 'text-yellow-400'
                      }`} />
                      <div className="flex-1">
                        <p className="text-sm text-slate-200 font-medium">{sugg.text}</p>
                        <p className="text-xs text-slate-500 mt-1">{sugg.timestamp}</p>
                      </div>
                    </div>
                  </div>
                ))}

                {/* Messages du chat */}
                {messages.map((msg, idx) => (
                  <div
                    key={idx}
                    className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    {msg.role === 'assistant' && (
                      <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center flex-shrink-0">
                        <Sparkles className="w-4 h-4 text-white" />
                      </div>
                    )}
                    <div
                      className={`max-w-[80%] rounded-lg p-3 ${
                        msg.role === 'user'
                          ? 'bg-blue-600 text-white'
                          : 'bg-slate-700 text-slate-200'
                      }`}
                    >
                      <p className="text-sm">{msg.content}</p>
                      <p className="text-xs mt-1 opacity-70">{msg.timestamp}</p>
                    </div>
                    {msg.role === 'user' && (
                      <div className="w-8 h-8 bg-slate-600 rounded-lg flex items-center justify-center flex-shrink-0">
                        <User className="w-4 h-4 text-white" />
                      </div>
                    )}
                  </div>
                ))}
                <div ref={messagesEndRef} />
              </>
            )}
          </div>

          {/* Input */}
          <div className="flex-shrink-0 border-t border-slate-700/50 p-3 bg-slate-900/30">
            <form onSubmit={handleSendMessage} className="flex gap-2">
              <input
                type="text"
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                placeholder="Posez une question à l'assistant..."
                className="flex-1 bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
              />
              <button
                type="submit"
                disabled={!inputMessage.trim()}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Send className="w-4 h-4" />
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  )
}