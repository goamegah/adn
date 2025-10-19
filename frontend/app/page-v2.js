'use client'
import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { PatientSynthesis, DiagnosticDifferentials, CriticalAlerts, ImmediateRecommendations } from '../components/PanelsNew'
import ChatPro from '../components/ChatPro'
import { analyze } from '../lib/api'
import { Brain, Loader2, Activity } from '../components/icons'

export default function HomePro() {
  const [patientId, setPatientId] = useState('PAT-2024-1847')
  const [loading, setLoading] = useState(false)
  const [data, setData] = useState(null)
  const [streamingStep, setStreamingStep] = useState(null) // 'synthesis' | 'diagnostics' | 'alerts' | 'recommendations'
  const [chatHistory, setChatHistory] = useState([])

  // Simulation du streaming progressif des panels
  const simulateStreaming = async (responseData) => {
    setData(null)
    setStreamingStep('synthesis')
    
    // Étape 1: Synthèse Patient
    await new Promise(resolve => setTimeout(resolve, 800))
    setData({ patient_summary: responseData.patient_summary })
    
    // Étape 2: Diagnostics
    setStreamingStep('diagnostics')
    await new Promise(resolve => setTimeout(resolve, 1000))
    setData(prev => ({ ...prev, differentials: responseData.differentials }))
    
    // Étape 3: Alertes
    setStreamingStep('alerts')
    await new Promise(resolve => setTimeout(resolve, 600))
    setData(prev => ({ ...prev, alerts: responseData.alerts }))
    
    // Étape 4: Recommandations
    setStreamingStep('recommendations')
    await new Promise(resolve => setTimeout(resolve, 800))
    setData(prev => ({ ...prev, recommendations: responseData.recommendations, ...responseData }))
    
    setStreamingStep(null)
  }

  const handleChatMessage = async (text) => {
    setLoading(true)
    try {
      const res = await analyze(patientId, text)
      
      // Simuler le streaming
      await simulateStreaming(res)
      
      // Retourner le message de confirmation
      return `✅ Analyse terminée pour **${patientId}**.\n\n📊 **Résultats:**\n- ${res.differentials?.length || 0} diagnostics différentiels\n- ${res.alerts?.length || 0} alertes identifiées\n- ${res.recommendations?.length || 0} recommandations\n\nQue souhaitez-vous explorer ?`
    } catch (e) {
      return `❌ Erreur: ${e.message || String(e)}`
    } finally {
      setLoading(false)
    }
  }

  // Animation variants
  const panelVariants = {
    hidden: { opacity: 0, x: 50, scale: 0.95 },
    visible: { 
      opacity: 1, 
      x: 0, 
      scale: 1,
      transition: { duration: 0.5, ease: 'easeOut' }
    },
    exit: { opacity: 0, x: -50, scale: 0.95 }
  }

  const skeletonVariants = {
    pulse: {
      opacity: [0.5, 1, 0.5],
      transition: { duration: 1.5, repeat: Infinity, ease: 'easeInOut' }
    }
  }

  return (
    <div className="h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white flex flex-col overflow-hidden">
      {/* Header */}
      <header className="flex-shrink-0 border-b border-slate-700/50 bg-slate-900/50 backdrop-blur-sm">
        <div className="px-4 md:px-6 py-3 md:py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-blue-500 rounded-lg flex items-center justify-center shadow-lg shadow-blue-500/20">
              <Brain className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-lg md:text-xl font-bold">ADN Pro</h1>
              <p className="text-slate-400 text-xs hidden md:block">Architecture Orchestrateur — Split View</p>
            </div>
          </div>
          <div className="flex items-center gap-4 text-xs md:text-sm">
            <span className="flex items-center gap-2 text-slate-400">
              <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></span>
              Backend Actif
            </span>
            {data && (
              <span className="hidden md:flex items-center gap-2 text-slate-400">
                <Activity className="w-4 h-4" />
                {data.processing_time_ms}ms
              </span>
            )}
          </div>
        </div>
      </header>

      {/* Main Split View */}
      <div className="flex-1 flex flex-col lg:flex-row overflow-hidden">
        {/* LEFT: Chat Panel (40%) */}
        <div className="w-full lg:w-2/5 border-r border-slate-700/50 flex flex-col bg-slate-900/30 backdrop-blur-sm">
          <div className="flex-shrink-0 px-4 py-3 border-b border-slate-700/50">
            <input
              type="text"
              value={patientId}
              onChange={(e) => setPatientId(e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 transition-colors"
              placeholder="ID Patient"
            />
          </div>
          
          <div className="flex-1 overflow-hidden">
            <ChatPro 
              onSend={handleChatMessage}
              loading={loading}
              suggestions={[
                "Analyser les signes vitaux",
                "Quels examens complémentaires ?",
                "Risque d'interactions médicamenteuses ?",
                "Diagnostic le plus probable ?"
              ]}
            />
          </div>
        </div>

        {/* RIGHT: Results Panels (60%) */}
        <div className="flex-1 overflow-y-auto bg-slate-900/20 p-4 md:p-6">
          <AnimatePresence mode="wait">
            {!data && !loading && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="h-full flex flex-col items-center justify-center text-center"
              >
                <Brain className="w-16 h-16 text-slate-600 mb-4" />
                <p className="text-slate-400 text-lg font-medium mb-2">
                  Système d'Aide à la Décision Médicale
                </p>
                <p className="text-slate-500 text-sm max-w-md">
                  Posez une question ou décrivez un cas clinique dans le chat.
                  L'orchestrateur générera automatiquement les analyses des 4 agents spécialisés.
                </p>
              </motion.div>
            )}

            {(data || loading) && (
              <div className="space-y-4 md:space-y-6 max-w-5xl">
                {/* Panel 1: Synthèse Patient */}
                <AnimatePresence>
                  {(data?.patient_summary || streamingStep === 'synthesis') && (
                    <motion.div
                      variants={panelVariants}
                      initial="hidden"
                      animate="visible"
                      exit="exit"
                    >
                      {data?.patient_summary ? (
                        <PatientSynthesis data={data.patient_summary} />
                      ) : (
                        <SkeletonPanel title="🧠 Synthèse Patient" />
                      )}
                    </motion.div>
                  )}
                </AnimatePresence>

                {/* Panel 2: Diagnostics Différentiels */}
                <AnimatePresence>
                  {(data?.differentials || streamingStep === 'diagnostics') && (
                    <motion.div
                      variants={panelVariants}
                      initial="hidden"
                      animate="visible"
                      exit="exit"
                    >
                      {data?.differentials ? (
                        <DiagnosticDifferentials data={data.differentials} />
                      ) : (
                        <SkeletonPanel title="🔍 Diagnostics Différentiels" />
                      )}
                    </motion.div>
                  )}
                </AnimatePresence>

                {/* Panel 3: Alertes Critiques */}
                <AnimatePresence>
                  {(data?.alerts || streamingStep === 'alerts') && (
                    <motion.div
                      variants={panelVariants}
                      initial="hidden"
                      animate="visible"
                      exit="exit"
                    >
                      {data?.alerts ? (
                        <CriticalAlerts data={data.alerts} />
                      ) : (
                        <SkeletonPanel title="⚠️ Alertes Critiques" />
                      )}
                    </motion.div>
                  )}
                </AnimatePresence>

                {/* Panel 4: Recommandations */}
                <AnimatePresence>
                  {(data?.recommendations || streamingStep === 'recommendations') && (
                    <motion.div
                      variants={panelVariants}
                      initial="hidden"
                      animate="visible"
                      exit="exit"
                    >
                      {data?.recommendations ? (
                        <ImmediateRecommendations data={data.recommendations} />
                      ) : (
                        <SkeletonPanel title="💡 Recommandations Immédiates" />
                      )}
                    </motion.div>
                  )}
                </AnimatePresence>

                {/* Performance Metrics */}
                {data && data.analysis_id && (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="flex flex-wrap items-center gap-4 text-xs text-slate-500 pt-4 border-t border-slate-700/50"
                  >
                    <span>ID: {data.analysis_id}</span>
                    {data.confidence && <span>Confiance: {(data.confidence * 100).toFixed(0)}%</span>}
                    {data.processing_time_ms && <span>Temps: {data.processing_time_ms}ms</span>}
                  </motion.div>
                )}
              </div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  )
}

// Composant Skeleton pour le loading
function SkeletonPanel({ title }) {
  return (
    <motion.div
      variants={{
        pulse: {
          opacity: [0.5, 1, 0.5],
          transition: { duration: 1.5, repeat: Infinity, ease: 'easeInOut' }
        }
      }}
      animate="pulse"
      className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-6 backdrop-blur-sm"
    >
      <div className="flex items-center gap-3 mb-4">
        <div className="w-10 h-10 bg-slate-700/50 rounded-lg animate-pulse"></div>
        <div className="flex-1">
          <div className="h-5 bg-slate-700/50 rounded w-1/3 mb-2 animate-pulse"></div>
          <div className="h-3 bg-slate-700/30 rounded w-2/3 animate-pulse"></div>
        </div>
      </div>
      <div className="space-y-3">
        <div className="h-4 bg-slate-700/30 rounded animate-pulse"></div>
        <div className="h-4 bg-slate-700/30 rounded w-5/6 animate-pulse"></div>
        <div className="h-4 bg-slate-700/30 rounded w-4/6 animate-pulse"></div>
      </div>
    </motion.div>
  )
}
