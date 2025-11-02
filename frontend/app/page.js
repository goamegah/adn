'use client'
import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import Panels from '../components/Panels'
import ARMPanel from '../components/ARMPanel'
import SessionManager from '../components/SessionManager'
import { Brain, Phone, Settings, MessageCircle } from '../components/icons'

export default function Home() {
  const [activeTab, setActiveTab] = useState('session') // Défaut: Session
  const [view, setView] = useState('chat') // 'chat' | 'results' pour mobile
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [resultsCount, setResultsCount] = useState(0)
  const [currentSession, setCurrentSession] = useState(null)
  const [isDesktop, setIsDesktop] = useState(false)

  // Détection desktop
  useEffect(() => {
    const checkDesktop = () => setIsDesktop(window.innerWidth >= 1024)
    checkDesktop()
    window.addEventListener('resize', checkDesktop)
    return () => window.removeEventListener('resize', checkDesktop)
  }, [])

  const handleSessionCreated = (sessionId, responseData) => {
    setCurrentSession({ id: sessionId, data: responseData })
    console.log('✅ Session créée:', sessionId)
  }

  // Handler pour l'onglet Session
  const handleMessageSent = async (messageText) => {
    console.log('💬 Message reçu:', messageText)
    setLoading(true)
    
    try {
      // Attendre que les agents finissent de traiter
      console.log('⏳ Attente du traitement par les agents (2s)...')
      await new Promise(resolve => setTimeout(resolve, 2000))
      
      // Récupérer les outputs structurés des agents
      console.log('📡 Récupération des outputs des agents...')
      const { getAgentOutputs } = await import('../lib/api')
      const agentData = await getAgentOutputs()
      
      console.log('📊 Agent outputs reçus:', agentData)
      console.log('📊 Available outputs:', agentData?.available_outputs)
      
      // Vérifier que les données sont disponibles
      if (!agentData || !agentData.available_outputs || agentData.available_outputs.length === 0) {
        console.warn('⚠️ Aucun output disponible')
      } else {
        console.log('✅ Outputs disponibles:', agentData.available_outputs.join(', '))
      }
      
      // Stocker les données
      setData(agentData)
      
      // Compter les résultats
      const count = [
        agentData.patient,
        agentData.synthesis,
        agentData.expert
      ].filter(Boolean).length
      
      setResultsCount(count)
      console.log(`✅ ${count} agents ont produit des données`)
      
      // Basculer vers la vue résultats sur mobile
      if (typeof window !== 'undefined' && window.innerWidth < 1024) {
        setTimeout(() => setView('results'), 500)
      }
      
    } catch (error) {
      console.error('❌ Erreur lors de la récupération des outputs:', error)
      setData(null)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white">
      {/* Header */}
      <header className="border-b border-slate-700/50 bg-slate-900/50 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 py-3 md:py-4">
          <div className="flex items-center justify-between">
            {/* Logo */}
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                <Brain className="w-6 h-6" />
              </div>
              <div>
                <h1 className="text-lg md:text-xl font-bold">ADN</h1>
                <p className="text-xs text-slate-400">Agentic Diagnostic Navigator</p>
              </div>
            </div>
            
            {/* Navigation Tabs - Seulement ARM et Session */}
            <nav className="flex gap-1 bg-slate-800/50 rounded-lg p-1">
              {/* Onglet ARM */}
              <button
                onClick={() => {
                  setActiveTab('arm')
                  setData(null)
                }}
                className={`px-3 md:px-4 py-1.5 md:py-2 rounded-md text-xs md:text-sm font-medium transition-all flex items-center gap-2 ${
                  activeTab === 'arm' 
                    ? 'bg-blue-600 text-white' 
                    : 'text-slate-400 hover:text-white hover:bg-slate-700/50'
                }`}
              >
                <Phone className="w-4 h-4" />
                <span className="hidden sm:inline">ARM</span>
              </button>
              
              {/* Onglet Session */}
              <button
                onClick={() => {
                  setActiveTab('session')
                  setData(null)
                }}
                className={`px-3 md:px-4 py-1.5 md:py-2 rounded-md text-xs md:text-sm font-medium transition-all flex items-center gap-2 ${
                  activeTab === 'session' 
                    ? 'bg-blue-600 text-white' 
                    : 'text-slate-400 hover:text-white hover:bg-slate-700/50'
                }`}
              >
                <Settings className="w-4 h-4" />
                <span className="hidden sm:inline">Session</span>
              </button>
            </nav>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="h-[calc(100vh-73px)] md:h-[calc(100vh-81px)] overflow-hidden">
        <AnimatePresence mode="wait">
          
          {/* ARM Tab */}
          {activeTab === 'arm' && (
            <motion.div
              key="arm"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              transition={{ duration: 0.2 }}
              className="h-full"
            >
              <ARMPanel />
            </motion.div>
          )}
          
          {/* Session Tab */}
          {activeTab === 'session' && (
            <motion.div
              key="session"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              transition={{ duration: 0.2 }}
              className="h-full flex flex-col lg:flex-row"
            >
              {/* Chat Panel - Gauche (40%) */}
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
                    <SessionManager 
                      onSessionCreated={handleSessionCreated}
                      onMessageSent={handleMessageSent}
                    />
                  </motion.div>
                )}
              </AnimatePresence>

              {/* Results Panel - Droite (60%) */}
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
                    <div className="space-y-6 max-w-5xl w-full">
                      {/* État vide */}
                      {!data && !loading && (
                        <motion.div
                          initial={{ opacity: 0 }}
                          animate={{ opacity: 1 }}
                          className="w-full h-full flex flex-col items-center justify-center text-center px-4"
                        >
                          <Brain className="w-12 h-12 lg:w-16 lg:h-16 text-slate-600 mb-4" />
                          <p className="text-slate-400 text-base lg:text-lg font-medium mb-2">
                            Résultats des Agents
                          </p>
                          <p className="text-slate-500 text-sm max-w-md">
                            Envoyez un message dans le chat pour analyser un patient.
                            Les résultats des 3 agents apparaîtront ici avec les alertes.
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

                      {/* Loading */}
                      {loading && (
                        <motion.div
                          initial={{ opacity: 0 }}
                          animate={{ opacity: 1 }}
                          className="w-full h-full flex flex-col items-center justify-center"
                        >
                          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-500 mb-4"></div>
                          <p className="text-slate-400 text-lg font-medium">Analyse en cours...</p>
                          <p className="text-slate-500 text-sm mt-2">Les agents traitent votre requête</p>
                        </motion.div>
                      )}

                      {/* Résultats avec Panels */}
                      {data && !loading && (
                        <motion.div
                          initial={{ opacity: 0, y: 20 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ duration: 0.4 }}
                        >
                          <Panels data={data} />
                          
                          {/* Performance Metrics */}
                          {resultsCount > 0 && (
                            <motion.div
                              initial={{ opacity: 0 }}
                              animate={{ opacity: 1 }}
                              className="flex flex-wrap items-center gap-4 text-xs text-slate-500 pt-4 border-t border-slate-700/50 mt-6"
                            >
                              <span>✅ {resultsCount} agents actifs</span>
                              {data.processing_time_ms && <span>⏱️ {data.processing_time_ms}ms</span>}
                            </motion.div>
                          )}
                        </motion.div>
                      )}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>

              {/* Mobile FAB pour revenir au chat */}
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
            </motion.div>
          )}
          
        </AnimatePresence>
      </div>
    </div>
  )
}