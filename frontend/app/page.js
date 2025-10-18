'use client'
import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { PatientSynthesis, DiagnosticDifferentials, CriticalAlerts, ImmediateRecommendations } from '../components/PanelsNew'
import ChatPro from '../components/ChatPro'
import { analyze } from '../lib/api'
import { Brain, Activity, MessageCircle, BarChart3 } from '../components/icons'

export default function Home() {
  const [patientId, setPatientId] = useState('PAT-2024-1847')
  const [view, setView] = useState('chat') // 'chat' | 'results' for mobile
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [streamingStep, setStreamingStep] = useState(null)
  const [resultsCount, setResultsCount] = useState(0)
  const [isDesktop, setIsDesktop] = useState(false)

  // Détecter la taille d'écran côté client
  useEffect(() => {
    const checkDesktop = () => setIsDesktop(window.innerWidth >= 1024)
    checkDesktop()
    window.addEventListener('resize', checkDesktop)
    return () => window.removeEventListener('resize', checkDesktop)
  }, [])

  // Simulation du streaming progressif
  const simulateStreaming = async (responseData) => {
    setData(null)
    setStreamingStep('synthesis')
    
    await new Promise(resolve => setTimeout(resolve, 800))
    setData({ patient_summary: responseData.patient_summary })
    
    setStreamingStep('diagnostics')
    await new Promise(resolve => setTimeout(resolve, 1000))
    setData(prev => ({ ...prev, differentials: responseData.differentials }))
    
    setStreamingStep('alerts')
    await new Promise(resolve => setTimeout(resolve, 600))
    setData(prev => ({ ...prev, alerts: responseData.alerts }))
    
    setStreamingStep('recommendations')
    await new Promise(resolve => setTimeout(resolve, 800))
    setData(prev => ({ ...prev, recommendations: responseData.recommendations, ...responseData }))
    
    setStreamingStep(null)
  }

  const handleChatMessage = async (text) => {
    setLoading(true)
    try {
      const res = await analyze(patientId, text)
      
      await simulateStreaming(res)
      
      // Compter les résultats pour le badge
      const count = [
        res.patient_summary,
        res.differentials,
        res.alerts,
        res.recommendations
      ].filter(Boolean).length
      setResultsCount(count)
      
      // Sur mobile, suggérer de voir les résultats
      if (typeof window !== 'undefined' && window.innerWidth < 1024) {
        setTimeout(() => setView('results'), 1000)
      }
      
      return `✅ Analyse terminée pour **${patientId}**.\n\n📊 **Résultats:**\n- ${res.differentials?.length || 0} diagnostics différentiels\n- ${res.alerts?.length || 0} alertes identifiées\n- ${res.recommendations?.length || 0} recommandations\n\nQue souhaitez-vous explorer ?`
    } catch (e) {
      return `❌ Erreur: ${e.message || String(e)}`
    } finally {
      setLoading(false)
    }
  }

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

  return (
    <div className="h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white flex flex-col overflow-hidden">
      {/* Header */}
      <header className="flex-shrink-0 border-b border-slate-700/50 bg-slate-900/50 backdrop-blur-sm">
        <div className="px-4 md:px-6 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 lg:w-10 lg:h-10 bg-gradient-to-br from-blue-600 to-blue-500 rounded-lg flex items-center justify-center shadow-lg shadow-blue-500/20">
              <Brain className="w-5 h-5 lg:w-6 lg:h-6" />
            </div>
            <div>
              <h1 className="text-base lg:text-lg font-bold">ADN Pro</h1>
              <p className="text-slate-400 text-xs hidden md:block">Split View Mobile-Ready</p>
            </div>
          </div>
          <div className="flex items-center gap-3 text-xs">
            <span className="flex items-center gap-2 text-slate-400">
              <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></span>
              <span className="hidden sm:inline">Backend</span>
            </span>
            {data && (
              <span className="hidden md:flex items-center gap-2 text-slate-400">
                <Activity className="w-4 h-4" />
                {data.processing_time_ms}ms
              </span>
            )}
          </div>
        </div>

        {/* Mobile Tabs */}
        <div className="lg:hidden flex border-t border-slate-700/50">
          <button
            onClick={() => setView('chat')}
            className={`flex-1 py-3 text-sm font-medium transition-colors relative ${
              view === 'chat' 
                ? 'text-blue-400 bg-slate-800/50' 
                : 'text-slate-400 hover:text-slate-300'
            }`}
          >
            <div className="flex items-center justify-center gap-2">
              <MessageCircle className="w-4 h-4" />
              <span>Chat</span>
            </div>
            {view === 'chat' && (
              <motion.div
                layoutId="activeTab"
                className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-400"
                initial={false}
                transition={{ duration: 0.3 }}
              />
            )}
          </button>
          <button
            onClick={() => setView('results')}
            className={`flex-1 py-3 text-sm font-medium transition-colors relative ${
              view === 'results' 
                ? 'text-blue-400 bg-slate-800/50' 
                : 'text-slate-400 hover:text-slate-300'
            }`}
          >
            <div className="flex items-center justify-center gap-2">
              <BarChart3 className="w-4 h-4" />
              <span>Résultats</span>
              {resultsCount > 0 && (
                <span className="px-1.5 py-0.5 bg-blue-600 rounded-full text-xs min-w-[1.25rem] text-center">
                  {resultsCount}
                </span>
              )}
            </div>
            {view === 'results' && (
              <motion.div
                layoutId="activeTab"
                className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-400"
                initial={false}
                transition={{ duration: 0.3 }}
              />
            )}
          </button>
        </div>
      </header>

      {/* Main Split View */}
      <div className="flex-1 flex flex-col lg:flex-row overflow-hidden">
        {/* LEFT: Chat Panel (Mobile: Conditional, Desktop: Always visible) */}
        <AnimatePresence mode="wait">
          {(view === 'chat' || isDesktop) && (
            <motion.div
              initial={{ x: -20, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              exit={{ x: -20, opacity: 0 }}
              transition={{ duration: 0.2 }}
              className={`
                ${view === 'chat' ? 'flex' : 'hidden lg:flex'}
                w-full lg:w-2/5 border-r border-slate-700/50 flex-col bg-slate-900/30 backdrop-blur-sm
              `}
            >
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
            </motion.div>
          )}
        </AnimatePresence>

        {/* RIGHT: Results Panels (Mobile: Conditional, Desktop: Always visible) */}
        <AnimatePresence mode="wait">
          {(view === 'results' || isDesktop) && (
            <motion.div
              initial={{ x: 20, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              exit={{ x: 20, opacity: 0 }}
              transition={{ duration: 0.2 }}
              className={`
                ${view === 'results' ? 'flex' : 'hidden lg:flex'}
                flex-1 overflow-y-auto bg-slate-900/20 p-4 md:p-6
              `}
            >
              <AnimatePresence mode="wait">
                {!data && !loading && (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="w-full h-full flex flex-col items-center justify-center text-center px-4"
                  >
                    <Brain className="w-12 h-12 lg:w-16 lg:h-16 text-slate-600 mb-4" />
                    <p className="text-slate-400 text-base lg:text-lg font-medium mb-2">
                      Système d'Aide à la Décision Médicale
                    </p>
                    <p className="text-slate-500 text-sm max-w-md">
                      Posez une question ou décrivez un cas clinique dans le chat.
                      L'orchestrateur générera automatiquement les analyses des 4 agents spécialisés.
                    </p>
                    <button
                      onClick={() => setView('chat')}
                      className="lg:hidden mt-6 px-6 py-3 bg-blue-600 hover:bg-blue-700 rounded-lg font-medium flex items-center gap-2 transition-colors"
                    >
                      <MessageCircle className="w-5 h-5" />
                      Aller au Chat
                    </button>
                  </motion.div>
                )}

                {(data || loading) && (
                  <div className="space-y-4 md:space-y-6 max-w-5xl w-full">
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
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Mobile FAB - Retour au chat depuis résultats */}
      {view === 'results' && data && (
        <motion.button
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          exit={{ scale: 0 }}
          onClick={() => setView('chat')}
          className="lg:hidden fixed bottom-6 right-6 w-14 h-14 bg-blue-600 hover:bg-blue-700 rounded-full flex items-center justify-center shadow-lg shadow-blue-500/50 z-50"
        >
          <MessageCircle className="w-6 h-6" />
        </motion.button>
      )}
    </div>
  )
}

// Composant Skeleton pour le loading
function SkeletonPanel({ title }) {
  return (
    <motion.div
      animate={{
        opacity: [0.5, 1, 0.5],
      }}
      transition={{
        duration: 1.5,
        repeat: Infinity,
        ease: 'easeInOut'
      }}
      className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-4 md:p-6 backdrop-blur-sm"
    >
      <div className="flex items-center gap-3 mb-4">
        <div className="w-8 h-8 md:w-10 md:h-10 bg-slate-700/50 rounded-lg animate-pulse"></div>
        <div className="flex-1">
          <div className="h-4 md:h-5 bg-slate-700/50 rounded w-1/3 mb-2 animate-pulse"></div>
          <div className="h-3 bg-slate-700/30 rounded w-2/3 animate-pulse"></div>
        </div>
      </div>
      <div className="space-y-3">
        <div className="h-3 md:h-4 bg-slate-700/30 rounded animate-pulse"></div>
        <div className="h-3 md:h-4 bg-slate-700/30 rounded w-5/6 animate-pulse"></div>
        <div className="h-3 md:h-4 bg-slate-700/30 rounded w-4/6 animate-pulse"></div>
      </div>
    </motion.div>
  )
}
