/* Chat.jsx — Modern responsive chat interface */
'use client'
import { useState, useRef, useEffect } from 'react'

export default function Chat({ onSend }) {
  const [input, setInput] = useState('Bonjour, peux-tu analyser ce cas ?')
  const [messages, setMessages] = useState([])
  const [busy, setBusy] = useState(false)
  const messagesEndRef = useRef(null)

  // Auto-scroll vers le bas quand de nouveaux messages arrivent
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  async function handleSend(e) {
    e?.preventDefault()
    const text = input.trim()
    if (!text) return
    setMessages((m) => [...m, { role: 'user', text }])
    setInput('')
    if (!onSend) return
    setBusy(true)
    try {
      const reply = await onSend(text)
      setMessages((m) => [...m, { role: 'assistant', text: String(reply ?? '') }])
    } catch (err) {
      setMessages((m) => [
        ...m,
        { role: 'assistant', text: 'Erreur lors de l\'envoi: ' + (err?.message || String(err)) },
      ])
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="flex flex-col h-full w-full">
      <div className="flex-1 overflow-y-auto p-3 md:p-4 space-y-3">
        {messages.length === 0 ? (
          <div className="text-slate-400 text-xs md:text-sm text-center py-8">
            Démarrez la conversation. Votre message sera analysé par les agents.
          </div>
        ) : (
          <>
            {messages.map((m, i) => (
              <div
                key={i}
                className={`max-w-[85%] p-2.5 md:p-3 rounded-lg text-xs md:text-sm break-words ${
                  m.role === 'user'
                    ? 'ml-auto bg-gradient-to-r from-blue-600 to-blue-500 text-white'
                    : 'bg-slate-700/50 text-slate-200'
                }`}
              >
                <div className="whitespace-pre-wrap">{m.text}</div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>
      <form onSubmit={handleSend} className="p-3 md:p-4 border-t border-slate-700 flex gap-2 flex-shrink-0">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Écrire un message..."
          disabled={busy}
          className="flex-1 bg-slate-700 border border-slate-600 rounded-lg px-3 md:px-4 py-2 text-white placeholder-slate-400 focus:outline-none focus:border-blue-500 text-xs md:text-sm"
        />
        <button
          type="submit"
          disabled={busy || !input.trim()}
          className="px-3 md:px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-700 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg text-white font-medium transition-colors text-xs md:text-sm whitespace-nowrap"
        >
          {busy ? 'Envoi…' : 'Envoyer'}
        </button>
      </form>
    </div>
  )
}
