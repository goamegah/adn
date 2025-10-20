'use client'
import { useState, useEffect, useRef } from 'react'
import { Phone, Mic, Square, Activity, Brain, AlertCircle, User, Clock, Volume2, AlertTriangle } from './icons'

function AnimatePresence({ children }) {
  return <>{children}</>
}

function motion({ children, ...props }) {
  return <div {...props}>{children}</div>
}

motion.div = motion

export default function ARMPanel() {
  const [sessionId, setSessionId] = useState(null)
  const [isRecording, setIsRecording] = useState(false)
  const [transcript, setTranscript] = useState([])
  const [currentText, setCurrentText] = useState('')
  const [analysis, setAnalysis] = useState([])
  const [alerts, setAlerts] = useState([]) // 🆕 Alertes séparées
  const [callerInfo, setCallerInfo] = useState({ firstName: '', lastName: '', phone: '' })
  const [startTime, setStartTime] = useState(null)
  const [duration, setDuration] = useState(0)
  const transcriptEndRef = useRef(null)
  const analysisEndRef = useRef(null)

  // Auto-scroll
  useEffect(() => {
    transcriptEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [transcript, currentText])

  useEffect(() => {
    analysisEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [analysis, alerts]) // 🆕 Scroll aussi sur les alertes

  // Timer pour la durée d'appel
  useEffect(() => {
    if (!isRecording || !startTime) return

    const interval = setInterval(() => {
      setDuration(Math.floor((Date.now() - startTime) / 1000))
    }, 1000)

    return () => clearInterval(interval)
  }, [isRecording, startTime])

  // Polling du status
  useEffect(() => {
    if (!sessionId || !isRecording) return

    const interval = setInterval(async () => {
      try {
        const response = await fetch(`http://localhost:8000/call/status/${sessionId}`)
        if (response.ok) {
          const data = await response.json()
          
          // Filtrer les doublons et les textes "[en cours]"
          const cleanTranscript = (data.transcript || [])
            .filter(text => !text.startsWith('[en cours]'))
            .filter((text, index, self) => self.indexOf(text) === index)
          
          setTranscript(cleanTranscript)
          setCurrentText(data.current_text || '')
          setAnalysis(data.analysis || [])
          setAlerts(data.alerts || []) // 🆕 Récupérer les alertes
          
          if (!data.is_active) {
            setIsRecording(false)
            clearInterval(interval)
          }
        }
      } catch (error) {
        console.error('Error polling status:', error)
      }
    }, 1000)

    return () => clearInterval(interval)
  }, [sessionId, isRecording])

  const startCall = async () => {
    if (!callerInfo.firstName || !callerInfo.phone) {
      alert('Veuillez renseigner au minimum le prénom et le téléphone')
      return
    }

    try {
      const response = await fetch('http://localhost:8000/call/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(callerInfo)
      })

      if (response.ok) {
        const data = await response.json()
        setSessionId(data.session_id)
        setIsRecording(true)
        setStartTime(Date.now())
        setDuration(0)
        setTranscript([])
        setCurrentText('')
        setAnalysis([])
        setAlerts([]) // 🆕 Reset alertes
        console.log('📞 Call started:', data.session_id)
      }
    } catch (error) {
      console.error('Error starting call:', error)
      alert('Erreur lors du démarrage de l\'appel')
    }
  }

  const stopCall = async () => {
    if (!sessionId) return

    try {
      const response = await fetch(`http://localhost:8000/call/stop/${sessionId}`, {
        method: 'POST'
      })

      if (response.ok) {
        setIsRecording(false)
        console.log('🛑 Call stopped')
      }
    } catch (error) {
      console.error('Error stopping call:', error)
    }
  }

  const formatDuration = (seconds) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }

  // 🆕 Fonction pour déterminer l'icône d'alerte
  const getAlertIcon = (alert) => {
    if (alert.type === 'urgence') return <AlertCircle className="w-5 h-5 text-red-400" />
    if (alert.type === 'critique') return <AlertTriangle className="w-5 h-5 text-orange-400" />
    return <Activity className="w-5 h-5 text-yellow-400" />
  }

  // 🆕 Fonction pour déterminer la couleur d'alerte
  const getAlertColor = (alert) => {
    if (alert.type === 'urgence') return 'border-red-500/50 bg-red-500/10'
    if (alert.type === 'critique') return 'border-orange-500/50 bg-orange-500/10'
    return 'border-yellow-500/50 bg-yellow-500/10'
  }

  return (
    <div className="h-full flex flex-col bg-slate-900/20">
      {/* Header avec contrôles */}
      <div className="flex-shrink-0 bg-slate-800/50 border-b border-slate-700 p-4">
        {/* Informations appelant */}
        <div className="flex flex-col lg:flex-row gap-4 mb-4">
          <div className="flex-1 grid grid-cols-1 md:grid-cols-3 gap-3">
            <input
              type="text"
              placeholder="Prénom *"
              value={callerInfo.firstName}
              onChange={(e) => setCallerInfo({ ...callerInfo, firstName: e.target.value })}
              disabled={isRecording}
              className="bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-400 focus:outline-none focus:border-blue-500 disabled:opacity-50"
            />
            <input
              type="text"
              placeholder="Nom"
              value={callerInfo.lastName}
              onChange={(e) => setCallerInfo({ ...callerInfo, lastName: e.target.value })}
              disabled={isRecording}
              className="bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-400 focus:outline-none focus:border-blue-500 disabled:opacity-50"
            />
            <input
              type="tel"
              placeholder="Téléphone *"
              value={callerInfo.phone}
              onChange={(e) => setCallerInfo({ ...callerInfo, phone: e.target.value })}
              disabled={isRecording}
              className="bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-400 focus:outline-none focus:border-blue-500 disabled:opacity-50"
            />
          </div>

          {/* Boutons de contrôle */}
          <div className="flex gap-2">
            {!isRecording ? (
              <button
                onClick={startCall}
                className="flex items-center gap-2 px-6 py-2 bg-green-600 hover:bg-green-700 rounded-lg font-medium transition-colors text-sm whitespace-nowrap"
              >
                <Phone className="w-5 h-5" />
                Démarrer l'appel
              </button>
            ) : (
              <button
                onClick={stopCall}
                className="flex items-center gap-2 px-6 py-2 bg-red-600 hover:bg-red-700 rounded-lg font-medium transition-colors text-sm whitespace-nowrap"
              >
                <Square className="w-5 h-5" />
                Terminer l'appel
              </button>
            )}
          </div>
        </div>

        {/* Indicateur d'enregistrement */}
        {isRecording && (
          <div className="flex items-center justify-between bg-slate-900/50 rounded-lg p-3">
            <div className="flex items-center gap-3">
              <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse" />
              <div className="flex items-center gap-2">
                <Volume2 className="w-4 h-4 text-red-400" />
                <span className="text-red-400 font-medium text-sm">Enregistrement en cours</span>
              </div>
            </div>
            
            <div className="flex items-center gap-4 text-sm text-slate-300">
              <div className="flex items-center gap-2">
                <Clock className="w-4 h-4" />
                <span className="font-mono">{formatDuration(duration)}</span>
              </div>
              {callerInfo.firstName && (
                <div className="flex items-center gap-2">
                  <User className="w-4 h-4" />
                  <span>{callerInfo.firstName} {callerInfo.lastName}</span>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Split view: Transcript | Analysis */}
      <div className="flex-1 flex flex-col lg:flex-row overflow-hidden">
        {/* LEFT: Transcript */}
        <div className="flex-1 flex flex-col border-r border-slate-700">
          <div className="flex-shrink-0 bg-slate-800/30 border-b border-slate-700 px-4 py-3 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Mic className="w-5 h-5 text-blue-400" />
              <h3 className="font-semibold">Transcription en temps réel</h3>
            </div>
            <span className="text-xs text-slate-400 bg-slate-700/50 px-2 py-1 rounded">
              {transcript.length} phrase{transcript.length !== 1 ? 's' : ''}
            </span>
          </div>

          <div className="flex-1 overflow-y-auto p-4 space-y-3">
            {transcript.length === 0 && !currentText && (
              <div className="h-full flex items-center justify-center text-center">
                <div>
                  <Mic className="w-16 h-16 text-slate-600 mx-auto mb-4" />
                  <p className="text-slate-400 text-lg mb-2">
                    {isRecording 
                      ? "En attente de parole..."
                      : "Démarrez un appel pour voir la transcription"}
                  </p>
                  <p className="text-slate-500 text-sm">
                    {isRecording 
                      ? "La transcription apparaîtra ici en temps réel"
                      : "Les paroles de l'appelant seront transcrites automatiquement"}
                  </p>
                </div>
              </div>
            )}

            {/* Phrases finalisées */}
            {transcript.map((text, i) => (
              <div
                key={`final-${i}`}
                className="bg-slate-800/50 rounded-lg p-4 border-l-4 border-blue-500"
              >
                <div className="flex items-start gap-3">
                  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-500/20 flex items-center justify-center">
                    <span className="text-blue-400 text-xs font-bold">{i + 1}</span>
                  </div>
                  <div className="flex-1">
                    <p className="text-slate-200 text-sm leading-relaxed">{text}</p>
                  </div>
                </div>
              </div>
            ))}

            {/* Texte en cours (interim) */}
            {currentText && (
              <div className="bg-blue-500/5 border-2 border-blue-500/30 border-dashed rounded-lg p-4">
                <div className="flex items-start gap-3">
                  <div className="animate-pulse">
                    <Mic className="w-5 h-5 text-blue-400 flex-shrink-0 mt-0.5" />
                  </div>
                  <div className="flex-1">
                    <p className="text-blue-200 text-sm italic leading-relaxed">{currentText}</p>
                    <p className="text-blue-400/60 text-xs mt-2">En cours de transcription...</p>
                  </div>
                </div>
              </div>
            )}
            <div ref={transcriptEndRef} />
          </div>
        </div>

        {/* RIGHT: Analysis & Alerts */}
        <div className="flex-1 flex flex-col">
          <div className="flex-shrink-0 bg-slate-800/30 border-b border-slate-700 px-4 py-3 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Brain className="w-5 h-5 text-purple-400" />
              <h3 className="font-semibold">Analyse IA & Recommandations</h3>
            </div>
            <div className="flex items-center gap-2">
              {alerts.length > 0 && (
                <span className="text-xs text-red-400 bg-red-500/20 px-2 py-1 rounded font-semibold animate-pulse">
                  🚨 {alerts.length} alerte{alerts.length !== 1 ? 's' : ''}
                </span>
              )}
              <span className="text-xs text-slate-400 bg-slate-700/50 px-2 py-1 rounded">
                {analysis.length} insight{analysis.length !== 1 ? 's' : ''}
              </span>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto p-4 space-y-3">
            {/* État vide uniquement si vraiment aucune donnée */}
            {alerts.length === 0 && analysis.length === 0 && !isRecording && (
              <div className="h-full flex items-center justify-center text-center">
                <div>
                  <Brain className="w-16 h-16 text-slate-600 mx-auto mb-4" />
                  <p className="text-slate-400 text-lg mb-2">Analyses IA en attente</p>
                  <p className="text-slate-500 text-sm max-w-md mx-auto">
                    Les recommandations de l'IA s'afficheront en temps réel pendant l'appel
                  </p>
                </div>
              </div>
            )}

            {/* Message d'attente pendant l'enregistrement */}
            {alerts.length === 0 && analysis.length === 0 && isRecording && (
              <div className="h-full flex items-center justify-center text-center">
                <div>
                  <div className="w-16 h-16 mx-auto mb-4 animate-pulse">
                    <Brain className="w-16 h-16 text-blue-400" />
                  </div>
                  <p className="text-blue-400 text-lg mb-2 animate-pulse">
                    Analyse en cours...
                  </p>
                  <p className="text-slate-400 text-sm max-w-md mx-auto">
                    L'IA écoute et analyse chaque phrase en temps réel
                  </p>
                </div>
              </div>
            )}

            {/* 🆕 ALERTES CRITIQUES EN PREMIER - TOUJOURS AFFICHÉES */}
            {alerts.map((alert, i) => (
              <div
                key={`alert-${alert.timestamp}-${i}`}
                className={`rounded-lg border-2 p-4 ${getAlertColor(alert)} shadow-lg`}
                style={{
                  animation: 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite'
                }}
              >
                <div className="flex items-start gap-3">
                  <div className="flex-shrink-0">
                    {getAlertIcon(alert)}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <span className={`text-xs font-bold uppercase ${
                        alert.type === 'urgence' ? 'text-red-400' : 'text-orange-400'
                      }`}>
                        {alert.type === 'urgence' ? '🚨 URGENCE' : '⚠️ CRITIQUE'}
                      </span>
                      {alert.keyword && (
                        <span className="text-xs text-slate-400">
                          Mot-clé: "{alert.keyword}"
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-slate-200 leading-relaxed font-medium">
                      {alert.message}
                    </p>
                    <p className="text-xs text-slate-400 mt-2 italic">
                      Phrase: "{alert.text}"
                    </p>
                  </div>
                </div>
              </div>
            ))}

            {/* ANALYSES GÉNÉRALES - TOUJOURS AFFICHÉES */}
            {analysis.map((item, i) => (
              <div
                key={`analysis-${i}-${item.substring(0, 20)}`}
                className="rounded-lg border-2 border-blue-500/50 bg-blue-500/10 p-4"
              >
                <div className="flex items-start gap-3">
                  <div className="flex-shrink-0">
                    <Activity className="w-5 h-5 text-blue-400" />
                  </div>
                  <div className="flex-1">
                    <p className="text-sm text-slate-200 leading-relaxed">{item}</p>
                  </div>
                </div>
              </div>
            ))}
            
            <div ref={analysisEndRef} />
          </div>
        </div>
      </div>
    </div>
  )
}