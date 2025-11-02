/* SessionManager.jsx - Chat avec affichage des tool calls */
'use client'
import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { startSession, sendMessage, getExecutionTrace } from '../lib/api'
import { Send, Loader2, User, Brain, Sparkles, CheckCircle2, Zap } from './icons'

// Composant pour afficher les tool calls
function ToolCallDisplay({ toolCalls = [] }) {
  if (!toolCalls || toolCalls.length === 0) return null

  return (
    <div className="space-y-2 mb-3">
      {toolCalls.map((tool, idx) => {
        const isComplete = tool.status === 'completed' || tool.completed
        const isRunning = tool.status === 'running' || (!isComplete && idx === toolCalls.length - 1)
        
        return (
          <motion.div
            key={idx}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: idx * 0.1 }}
            className="flex items-center gap-2 text-sm"
          >
            {/* Icône de statut */}
            <div className="flex-shrink-0">
              {isRunning ? (
                <div className="w-5 h-5 rounded-full bg-green-500/20 flex items-center justify-center">
                  <Loader2 className="w-3 h-3 text-green-400 animate-spin" />
                </div>
              ) : isComplete ? (
                <div className="w-5 h-5 rounded-full bg-green-500/20 flex items-center justify-center">
                  <CheckCircle2 className="w-3 h-3 text-green-400" />
                </div>
              ) : (
                <div className="w-5 h-5 rounded-full bg-slate-700 flex items-center justify-center">
                  <Zap className="w-3 h-3 text-slate-400" />
                </div>
              )}
            </div>

            {/* Nom de l'outil */}
            <div className="flex-1 flex items-center gap-2">
              <span className="text-slate-300 font-mono text-xs">
                {tool.name || tool.tool_name || 'unknown_tool'}
              </span>
              {isRunning && (
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: 'auto' }}
                  className="flex gap-1"
                >
                  <span className="w-1.5 h-1.5 bg-green-400 rounded-full animate-pulse" />
                  <span className="w-1.5 h-1.5 bg-green-400 rounded-full animate-pulse" style={{ animationDelay: '75ms' }} />
                  <span className="w-1.5 h-1.5 bg-green-400 rounded-full animate-pulse" style={{ animationDelay: '150ms' }} />
                </motion.div>
              )}
            </div>
          </motion.div>
        )
      })}
    </div>
  )
}

export default function SessionManager({ onSessionCreated, onMessageSent }) {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: '👋 Bonjour ! Je suis l\'assistant ADN. Décrivez-moi un cas clinique ou posez-moi une question sur un patient.',
      timestamp: new Date()
    }
  ])
  const [input, setInput] = useState('')
  const [busy, setBusy] = useState(false)
  const [sessionActive, setSessionActive] = useState(false)
  const [sessionData, setSessionData] = useState(null)
  const [showInitPanel, setShowInitPanel] = useState(true)
  const [error, setError] = useState(null)
  const [currentToolCalls, setCurrentToolCalls] = useState([])
  
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, currentToolCalls])

  async function handleCreateSession() {
    setBusy(true)
    setError(null)

    try {
      const data = await startSession()
      
      const isSuccess = data.message || data.session_id || data.user_id
      
      if (!isSuccess && data.error) {
        throw new Error(data.error)
      }

      setSessionData(data)
      setSessionActive(true)
      setShowInitPanel(false)
      
      if (onSessionCreated) {
        onSessionCreated(data.session_id || 'session_api', data)
      }
    } catch (err) {
      setError(err.message || 'Erreur lors de la création de la session')
    } finally {
      setBusy(false)
    }
  }

  const handleSend = async (text = input) => {
    if (!text.trim() || busy) return

    const userMessage = {
      role: 'user',
      content: text,
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setBusy(true)
    setCurrentToolCalls([])

    try {
      // Lancer le message
      const replyPromise = sendMessage(text)
      
      // Polling pour récupérer les tool calls pendant l'exécution
      const pollInterval = setInterval(async () => {
        try {
          const trace = await getExecutionTrace('user_backend', 'session_api')
          if (trace?.trace?.tool_calls) {
            const tools = trace.trace.tool_calls.map(tc => ({
              name: tc.name || tc.tool_name,
              status: tc.status || 'completed',
              completed: tc.completed !== false
            }))
            setCurrentToolCalls(tools)
          }
        } catch (e) {
          console.log('Polling error:', e)
        }
      }, 500)

      const reply = await replyPromise
      clearInterval(pollInterval)
      
      // Marquer tous les tools comme completed
      if (currentToolCalls.length > 0) {
        setCurrentToolCalls(prev => prev.map(t => ({ ...t, status: 'completed', completed: true })))
      }
      
      const assistantMessage = {
        role: 'assistant',
        content: reply || '✅ Analyse terminée.',
        timestamp: new Date(),
        toolCalls: currentToolCalls.length > 0 ? [...currentToolCalls] : undefined
      }
      
      setMessages(prev => [...prev, assistantMessage])
      
      // Appeler le callback
      if (onMessageSent) {
        onMessageSent(text)
      }
      
      // Reset tool calls après 1 seconde
      setTimeout(() => setCurrentToolCalls([]), 1000)
    } catch (error) {
      const errorMessage = {
        role: 'assistant',
        content: `❌ Erreur: ${error.message}`,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
      setCurrentToolCalls([])
    } finally {
      setBusy(false)
      inputRef.current?.focus()
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  // Mode Initialisation
  if (!sessionActive || showInitPanel) {
    return (
      <div className="h-full flex items-center justify-center p-4 bg-slate-900/20">
        <div className="max-w-md w-full bg-slate-800/50 border border-slate-700/50 rounded-xl p-6 backdrop-blur-sm">
          <h2 className="text-xl font-bold mb-2">Gestion de Session</h2>
          <p className="text-slate-400 text-sm mb-6">
            Initialisez une session pour commencer à discuter avec l'agent clinique
          </p>

          <div className="mb-6 space-y-2 text-sm">
            <div className="flex justify-between py-2 border-b border-slate-700/50">
              <span className="text-slate-400">User ID:</span>
              <span className="text-white font-mono">user_backend</span>
            </div>
            <div className="flex justify-between py-2 border-b border-slate-700/50">
              <span className="text-slate-400">Session ID:</span>
              <span className="text-white font-mono">session_api</span>
            </div>
          </div>

          {error && (
            <div className="mb-4 p-3 bg-red-500/10 border border-red-500/50 rounded-lg">
              <p className="text-red-400 text-sm flex items-center gap-2">
                <span>⚠️</span>
                <span>{error}</span>
              </p>
            </div>
          )}

          <button
            onClick={handleCreateSession}
            disabled={busy}
            className="w-full py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-700 disabled:cursor-not-allowed rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
          >
            {busy ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Initialisation...</span>
              </>
            ) : (
              <span>Initialiser la session</span>
            )}
          </button>

          <p className="text-slate-500 text-xs text-center mt-4">
            Une fois la session initialisée, vous pourrez discuter avec l'agent
          </p>
        </div>
      </div>
    )
  }

  // Mode Chat (session active)
  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex-shrink-0 px-4 py-3 border-b border-slate-700/50 bg-slate-800/50">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-medium text-white">Agent Clinique</h3>
            <p className="text-xs text-slate-400">
              Session: {sessionData?.session_id || 'session_api'}
            </p>
          </div>
          <button
            onClick={() => setShowInitPanel(true)}
            className="text-xs text-slate-400 hover:text-slate-300 px-3 py-1.5 rounded-lg hover:bg-slate-700/50 transition-colors"
          >
            ⚙️ Config
          </button>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
        <AnimatePresence initial={false}>
          {messages.map((msg, idx) => (
            <motion.div
              key={idx}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3 }}
              className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}
            >
              {/* Avatar */}
              <div className={`flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center ${
                msg.role === 'user' 
                  ? 'bg-blue-600' 
                  : 'bg-gradient-to-br from-purple-600 to-blue-600'
              }`}>
                {msg.role === 'user' ? (
                  <User className="w-5 h-5" />
                ) : (
                  <Brain className="w-5 h-5" />
                )}
              </div>

              {/* Message Bubble */}
              <div className={`flex-1 max-w-[85%] ${msg.role === 'user' ? 'text-right' : 'text-left'}`}>
                {/* Tool Calls - affichés avant le message */}
                {msg.role === 'assistant' && msg.toolCalls && msg.toolCalls.length > 0 && (
                  <div className="mb-2">
                    <ToolCallDisplay toolCalls={msg.toolCalls} />
                  </div>
                )}

                <div className={`inline-block rounded-2xl px-4 py-3 ${
                  msg.role === 'user'
                    ? 'bg-blue-600 text-white'
                    : 'bg-slate-800 text-slate-100 border border-slate-700'
                }`}>
                  {msg.role === 'assistant' ? (
                    <div className="prose prose-invert prose-sm max-w-none">
                      <ReactMarkdown 
                        remarkPlugins={[remarkGfm]}
                        components={{
                          ul: ({node, ...props}) => <ul className="list-disc list-inside space-y-1 my-2" {...props} />,
                          ol: ({node, ...props}) => <ol className="list-decimal list-inside space-y-1 my-2" {...props} />,
                          li: ({node, ...props}) => <li className="text-sm" {...props} />,
                          a: ({node, ...props}) => <a className="text-blue-400 hover:underline" {...props} />,
                          code: ({node, inline, ...props}) => 
                            inline ? (
                              <code className="bg-slate-900 px-1.5 py-0.5 rounded text-xs" {...props} />
                            ) : (
                              <code className="block bg-slate-900 p-2 rounded text-xs overflow-x-auto" {...props} />
                            ),
                          table: ({node, ...props}) => <table className="min-w-full border border-slate-600 my-2" {...props} />,
                          th: ({node, ...props}) => <th className="border border-slate-600 px-2 py-1 bg-slate-700" {...props} />,
                          td: ({node, ...props}) => <td className="border border-slate-600 px-2 py-1" {...props} />,
                        }}
                      >
                        {msg.content}
                      </ReactMarkdown>
                    </div>
                  ) : (
                    <p className="text-sm whitespace-pre-wrap break-words">{msg.content}</p>
                  )}
                </div>
                <div className="text-xs text-slate-500 mt-1 px-2">
                  {msg.timestamp.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}
                </div>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {/* Loading Indicator avec tool calls */}
        {busy && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex gap-3"
          >
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-purple-600 to-blue-600 flex items-center justify-center">
              <Brain className="w-5 h-5" />
            </div>
            <div className="bg-slate-800 border border-slate-700 rounded-2xl px-4 py-3 min-w-[200px]">
              {currentToolCalls.length > 0 ? (
                <ToolCallDisplay toolCalls={currentToolCalls} />
              ) : (
                <div className="flex items-center gap-2 text-slate-400">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span className="text-sm">Analyse en cours...</span>
                </div>
              )}
            </div>
          </motion.div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Quick Suggestions */}
      {messages.length === 1 && (
        <div className="flex-shrink-0 px-4 pb-3">
          <div className="flex items-center gap-2 mb-2">
            <Sparkles className="w-4 h-4 text-blue-400" />
            <span className="text-xs text-slate-400 font-medium">Questions suggérées</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {[
              "Analyser le patient 10006",
              "Quels sont les signes vitaux critiques ?",
              "Recommandations thérapeutiques ?",
            ].map((suggestion, idx) => (
              <button
                key={idx}
                onClick={() => handleSend(suggestion)}
                disabled={busy}
                className="text-xs px-3 py-1.5 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-full text-slate-300 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {suggestion}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input Area */}
      <div className="flex-shrink-0 border-t border-slate-700/50 p-4 bg-slate-900/50 backdrop-blur-sm">
        <div className="flex gap-2">
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Décrivez le cas clinique ou posez une question..."
            disabled={busy}
            className="flex-1 bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 resize-none disabled:opacity-50 disabled:cursor-not-allowed"
            rows="2"
          />
          <button
            onClick={() => handleSend()}
            disabled={busy || !input.trim()}
            className="self-end px-4 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-700 rounded-lg transition-colors disabled:cursor-not-allowed flex items-center justify-center"
          >
            {busy ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Send className="w-5 h-5" />
            )}
          </button>
        </div>
        <div className="flex items-center justify-between mt-2 text-xs text-slate-500">
          <span>Appuyez sur Entrée pour envoyer</span>
          {busy && <span className="text-blue-400">● Traitement backend...</span>}
        </div>
      </div>
    </div>
  )
}