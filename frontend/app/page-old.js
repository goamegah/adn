'use client'
import { useState } from 'react'
import { PatientSynthesis, DiagnosticDifferentials, CriticalAlerts, ImmediateRecommendations } from '../components/PanelsNew'
import Chat from '../components/Chat'
import { analyze } from '../lib/api'
import { Brain, Loader2, MessageCircle, X } from '../components/icons'

export default function Home() {
  const [patientId, setPatientId] = useState('PAT-2024-1847')
  const [query, setQuery] = useState('Analyse patient avec dyspnée aiguë')
  const [loading, setLoading] = useState(false)
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [chatOpen, setChatOpen] = useState(false)

  async function handleAnalyze() {
    setLoading(true)
    setError(null)
    try {
      const res = await analyze(patientId, query)
      setData(res)
    } catch (e) {
      setError(e.message || String(e))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white p-4 md:p-6">
      {/* Header */}
      <div className="max-w-7xl mx-auto mb-6 md:mb-8">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between mb-6 gap-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 md:w-12 md:h-12 bg-blue-600 rounded-lg flex items-center justify-center flex-shrink-0">
              <Brain className="w-6 h-6 md:w-7 md:h-7" />
            </div>
            <div>
              <h1 className="text-xl md:text-2xl font-bold">Agentic Diagnostic Navigator</h1>
              <p className="text-slate-400 text-xs md:text-sm">Architecture Orchestrateur — Prototype v1</p>
            </div>
          </div>
          <div className="flex items-center gap-3 md:gap-4 text-xs md:text-sm">
            <span className="text-slate-400">
              <span className="text-green-400">●</span> Backend Actif
            </span>
            <span className="text-slate-400 hidden sm:inline">Service: Urgences</span>
          </div>
        </div>

        {/* Search Bar */}
        <div className="space-y-3">
          <input
            type="text"
            value={patientId}
            onChange={(e) => setPatientId(e.target.value)}
            className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 text-sm md:text-base"
            placeholder="ID Patient (ex: PAT-2024-1847)"
          />
          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 h-20 md:h-24 resize-none text-sm md:text-base"
            placeholder="Prompt clinique (ex: patient avec dyspnée, fièvre, tachycardie...)"
          />
          <button
            onClick={handleAnalyze}
            disabled={loading}
            className="w-full bg-gradient-to-r from-blue-600 to-blue-500 hover:from-blue-700 hover:to-blue-600 disabled:from-slate-700 disabled:to-slate-700 px-6 md:px-8 py-3 md:py-4 rounded-lg font-semibold flex items-center justify-center gap-2 transition-all text-sm md:text-base"
          >
            {loading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Analyse en cours...
              </>
            ) : (
              <>
                <Brain className="w-5 h-5" />
                <span className="hidden sm:inline">Analyser avec ADN (4 agents)</span>
                <span className="sm:hidden">Analyser</span>
              </>
            )}
          </button>
        </div>

        {/* Error Display */}
        {error && (
          <div className="mt-4 bg-red-500/10 border border-red-500/50 rounded-lg p-3 text-red-300 text-sm">
            <strong>Erreur:</strong> {error}
          </div>
        )}

        {/* Indicateur de performance */}
        {data && (
          <div className="mt-4 flex flex-wrap items-center gap-3 md:gap-4 text-xs md:text-sm text-slate-400">
            <span>Analyse #{data.analysis_id || 'N/A'}</span>
            {data.confidence && <span>Confiance: {(data.confidence * 100).toFixed(0)}%</span>}
            {data.processing_time_ms && <span>Temps: {data.processing_time_ms}ms</span>}
          </div>
        )}
      </div>

      {/* Main Content Grid */}
      {data && (
        <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-4 md:gap-6 pb-20">
          {/* Left Column */}
          <div className="space-y-4 md:space-y-6">
            <PatientSynthesis data={data.patient_summary || data.summary || data.synthesis} />
            <CriticalAlerts data={data.alerts} />
          </div>

          {/* Right Column */}
          <div className="space-y-4 md:space-y-6">
            <DiagnosticDifferentials data={data.differentials || data.diagnostics} />
            <ImmediateRecommendations data={data.recommendations} />
          </div>
        </div>
      )}

      {/* Empty State */}
      {!data && !loading && (
        <div className="max-w-7xl mx-auto text-center py-12 md:py-20">
          <Brain className="w-12 h-12 md:w-16 md:h-16 text-slate-600 mx-auto mb-4" />
          <p className="text-slate-400 text-base md:text-lg">
            Entrez un ID patient et un prompt pour démarrer l'analyse
          </p>
          <p className="text-slate-500 text-xs md:text-sm mt-2">
            L'orchestrateur délèguera automatiquement aux 4 agents spécialisés
          </p>
        </div>
      )}

      {/* Floating Chat Button - Mobile Optimized */}
      {!chatOpen && (
        <button
          onClick={() => setChatOpen(true)}
          className="fixed right-4 bottom-4 md:right-6 md:bottom-6 w-12 h-12 md:w-14 md:h-14 bg-blue-600 hover:bg-blue-700 rounded-full flex items-center justify-center shadow-lg transition-all z-50"
        >
          <MessageCircle className="w-6 h-6" />
        </button>
      )}

      {/* Chat Overlay - Mobile First */}
      {chatOpen && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-end md:items-center justify-center p-0 md:p-4">
          <div className="bg-slate-800 border border-slate-700 rounded-t-2xl md:rounded-2xl w-full md:max-w-md max-w-full h-[85vh] md:h-[600px] flex flex-col shadow-2xl overflow-hidden">
            <div className="flex items-center justify-between p-4 border-b border-slate-700 flex-shrink-0">
              <div className="flex items-center gap-2">
                <MessageCircle className="w-5 h-5 text-blue-400" />
                <strong className="text-base md:text-lg">Assistant ADN</strong>
              </div>
              <button
                onClick={() => setChatOpen(false)}
                className="p-2 hover:bg-slate-700 rounded-lg transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="flex-1 min-h-0">
              <Chat
                onSend={async (text) => {
                  setLoading(true)
                  try {
                    const res = await analyze(patientId, text)
                    setData(res)
                    return res.chat_reply || 'Réponse reçue'
                  } catch (e) {
                    return 'Erreur: ' + (e.message || String(e))
                  } finally {
                    setLoading(false)
                  }
                }}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
