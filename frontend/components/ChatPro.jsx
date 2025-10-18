'use client'
import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Send, Loader2, User, Brain, Sparkles } from './icons'

export default function ChatPro({ onSend, loading = false, suggestions = [] }) {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: '👋 Bonjour ! Je suis l\'assistant ADN. Décrivez-moi un cas clinique ou posez-moi une question sur un patient.',
      timestamp: new Date()
    }
  ])
  const [input, setInput] = useState('')
  const [busy, setBusy] = useState(false)
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

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

    try {
      const reply = await onSend(text)
      
      const assistantMessage = {
        role: 'assistant',
        content: reply || '✅ Analyse terminée.',
        timestamp: new Date()
      }
      
      setMessages(prev => [...prev, assistantMessage])
    } catch (error) {
      const errorMessage = {
        role: 'assistant',
        content: `❌ Erreur: ${error.message}`,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
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

  return (
    <div className="h-full flex flex-col">
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
                          // Style personnalisé pour les listes
                          ul: ({node, ...props}) => <ul className="list-disc list-inside space-y-1 my-2" {...props} />,
                          ol: ({node, ...props}) => <ol className="list-decimal list-inside space-y-1 my-2" {...props} />,
                          li: ({node, ...props}) => <li className="text-sm" {...props} />,
                          // Style pour les liens
                          a: ({node, ...props}) => <a className="text-blue-400 hover:underline" {...props} />,
                          // Style pour le code inline
                          code: ({node, inline, ...props}) => 
                            inline ? (
                              <code className="bg-slate-900 px-1.5 py-0.5 rounded text-xs" {...props} />
                            ) : (
                              <code className="block bg-slate-900 p-2 rounded text-xs overflow-x-auto" {...props} />
                            ),
                          // Style pour les tableaux
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

        {/* Loading Indicator */}
        {busy && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex gap-3"
          >
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-purple-600 to-blue-600 flex items-center justify-center">
              <Brain className="w-5 h-5" />
            </div>
            <div className="bg-slate-800 border border-slate-700 rounded-2xl px-4 py-3">
              <div className="flex items-center gap-2 text-slate-400">
                <Loader2 className="w-4 h-4 animate-spin" />
                <span className="text-sm">Analyse en cours...</span>
              </div>
            </div>
          </motion.div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Quick Suggestions */}
      {suggestions.length > 0 && messages.length === 1 && (
        <div className="flex-shrink-0 px-4 pb-3">
          <div className="flex items-center gap-2 mb-2">
            <Sparkles className="w-4 h-4 text-blue-400" />
            <span className="text-xs text-slate-400 font-medium">Questions suggérées</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {suggestions.map((suggestion, idx) => (
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
          {loading && <span className="text-blue-400">● Traitement backend...</span>}
        </div>
      </div>
    </div>
  )
}
