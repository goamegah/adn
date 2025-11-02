/* ExecutionTrace.jsx - Style ADK Web avec icônes à gauche */
'use client'
import { useState } from 'react'

/**
 * Composant pour afficher la trace d'exécution style ADK Web
 * Affiche les tool calls avec icônes à gauche
 */
export default function ExecutionTrace({ trace, statistics }) {
  const [expandedItems, setExpandedItems] = useState({})

  if (!trace || !trace.timeline || trace.timeline.length === 0) {
    return (
      <div className="text-center text-slate-400 py-8">
        Aucune trace d'exécution disponible
      </div>
    )
  }

  const toggleItem = (index) => {
    setExpandedItems(prev => ({
      ...prev,
      [index]: !prev[index]
    }))
  }

  // Formater le timestamp
  const formatTime = (timestamp) => {
    if (!timestamp) return ''
    const date = new Date(timestamp)
    return date.toLocaleTimeString('fr-FR', { 
      hour: '2-digit', 
      minute: '2-digit', 
      second: '2-digit',
    })
  }

  // Grouper les tool calls et responses ensemble
  const groupedEvents = []
  let i = 0
  while (i < trace.timeline.length) {
    const event = trace.timeline[i]
    
    if (event.type === 'tool_call') {
      // Chercher la réponse correspondante
      let response = null
      for (let j = i + 1; j < trace.timeline.length; j++) {
        if (trace.timeline[j].type === 'tool_response' && 
            trace.timeline[j].description.includes(event.details?.name || '')) {
          response = trace.timeline[j]
          break
        }
      }
      
      groupedEvents.push({
        type: 'tool_execution',
        toolName: event.details?.name || event.description,
        call: event,
        response: response,
        timestamp: event.timestamp
      })
    } else if (event.type !== 'tool_response') {
      // Ajouter les autres événements tels quels
      groupedEvents.push(event)
    }
    
    i++
  }

  return (
    <div className="execution-trace-adk">
      {/* Header avec stats */}
      {statistics && (
        <div style={{
          padding: '12px 16px',
          backgroundColor: 'rgba(59, 130, 246, 0.1)',
          borderBottom: '1px solid rgba(148, 163, 184, 0.1)',
          marginBottom: '16px',
          fontSize: '0.875rem',
          color: 'var(--muted)'
        }}>
          <strong>{statistics.total_tool_calls}</strong> tool calls exécutés
        </div>
      )}

      {/* Timeline style ADK Web */}
      <div style={{position: 'relative'}}>
        {groupedEvents.map((event, index) => {
          if (event.type === 'tool_execution') {
            const isExpanded = expandedItems[index]
            const toolName = event.toolName
            const hasResponse = !!event.response
            
            return (
              <div key={index} style={{marginBottom: '8px'}}>
                {/* Tool Call - Icône éclair */}
                <div 
                  style={{
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: '12px',
                    padding: '8px 16px',
                    cursor: hasResponse ? 'pointer' : 'default'
                  }}
                  onClick={hasResponse ? () => toggleItem(index) : undefined}
                >
                  {/* Icône éclair dans un cercle vert */}
                  <div style={{
                    width: '32px',
                    height: '32px',
                    borderRadius: '50%',
                    backgroundColor: 'rgba(34, 197, 94, 0.2)',
                    border: '2px solid rgba(34, 197, 94, 0.4)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    flexShrink: 0,
                    marginTop: '4px'
                  }}>
                    <span style={{fontSize: '16px'}}>⚡</span>
                  </div>
                  
                  {/* Contenu */}
                  <div style={{flex: 1, minWidth: 0}}>
                    <div style={{
                      fontSize: '0.875rem',
                      fontWeight: 500,
                      color: '#e2e8f0',
                      fontFamily: 'monospace'
                    }}>
                      {toolName}
                    </div>
                    
                    {/* Arguments en petit si non étendu */}
                    {!isExpanded && event.call?.details && (
                      <div style={{
                        fontSize: '0.75rem',
                        color: 'var(--muted)',
                        marginTop: '4px',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap'
                      }}>
                        {JSON.stringify(event.call.details).substring(0, 80)}...
                      </div>
                    )}
                  </div>
                </div>

                {/* Détails expandables */}
                {isExpanded && event.call?.details && (
                  <div style={{
                    marginLeft: '44px',
                    marginTop: '8px',
                    marginBottom: '8px',
                    padding: '12px',
                    backgroundColor: 'rgba(15, 23, 42, 0.5)',
                    borderRadius: '6px',
                    border: '1px solid rgba(148, 163, 184, 0.1)'
                  }}>
                    <div style={{
                      fontSize: '0.75rem',
                      fontWeight: 600,
                      marginBottom: '8px',
                      color: '#3b82f6'
                    }}>
                      📥 Arguments:
                    </div>
                    <pre style={{
                      fontSize: '0.75rem',
                      color: 'var(--muted)',
                      overflow: 'auto',
                      maxHeight: '200px',
                      margin: 0,
                      whiteSpace: 'pre-wrap',
                      wordBreak: 'break-word'
                    }}>
                      {JSON.stringify(event.call.details, null, 2)}
                    </pre>
                  </div>
                )}

                {/* Tool Response - Icône check */}
                {hasResponse && (
                  <div 
                    style={{
                      display: 'flex',
                      alignItems: 'flex-start',
                      gap: '12px',
                      padding: '8px 16px',
                      marginTop: '4px',
                      cursor: 'pointer'
                    }}
                    onClick={() => toggleItem(index)}
                  >
                    {/* Icône check dans un cercle vert */}
                    <div style={{
                      width: '32px',
                      height: '32px',
                      borderRadius: '50%',
                      backgroundColor: 'rgba(34, 197, 94, 0.2)',
                      border: '2px solid rgba(34, 197, 94, 0.4)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      flexShrink: 0,
                      marginTop: '4px'
                    }}>
                      <span style={{fontSize: '16px', color: '#22c55e'}}>✓</span>
                    </div>
                    
                    {/* Contenu */}
                    <div style={{flex: 1, minWidth: 0}}>
                      <div style={{
                        fontSize: '0.875rem',
                        fontWeight: 500,
                        color: '#e2e8f0',
                        fontFamily: 'monospace'
                      }}>
                        {toolName}
                      </div>
                      
                      {!isExpanded && (
                        <div style={{
                          fontSize: '0.75rem',
                          color: 'var(--muted)',
                          marginTop: '4px'
                        }}>
                          Résultat disponible
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Résultat expandable */}
                {isExpanded && hasResponse && event.response?.details && (
                  <div style={{
                    marginLeft: '44px',
                    marginTop: '8px',
                    padding: '12px',
                    backgroundColor: 'rgba(15, 23, 42, 0.5)',
                    borderRadius: '6px',
                    border: '1px solid rgba(148, 163, 184, 0.1)'
                  }}>
                    <div style={{
                      fontSize: '0.75rem',
                      fontWeight: 600,
                      marginBottom: '8px',
                      color: '#22c55e'
                    }}>
                      📤 Résultat:
                    </div>
                    <pre style={{
                      fontSize: '0.75rem',
                      color: 'var(--muted)',
                      overflow: 'auto',
                      maxHeight: '300px',
                      margin: 0,
                      whiteSpace: 'pre-wrap',
                      wordBreak: 'break-word'
                    }}>
                      {JSON.stringify(event.response.details, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            )
          }
          
          // Autres événements (messages, etc.)
          return (
            <div 
              key={index}
              style={{
                display: 'flex',
                alignItems: 'flex-start',
                gap: '12px',
                padding: '8px 16px',
                marginBottom: '8px'
              }}
            >
              {/* Icône selon le type */}
              <div style={{
                width: '32px',
                height: '32px',
                borderRadius: '50%',
                backgroundColor: event.type === 'user_message' 
                  ? 'rgba(139, 92, 246, 0.2)' 
                  : 'rgba(245, 158, 11, 0.2)',
                border: `2px solid ${event.type === 'user_message' 
                  ? 'rgba(139, 92, 246, 0.4)' 
                  : 'rgba(245, 158, 11, 0.4)'}`,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0,
                marginTop: '4px'
              }}>
                <span style={{fontSize: '14px'}}>
                  {event.type === 'user_message' ? '👤' : '🤖'}
                </span>
              </div>
              
              {/* Contenu */}
              <div style={{flex: 1, minWidth: 0}}>
                <div style={{
                  fontSize: '0.875rem',
                  color: '#e2e8f0',
                  lineHeight: '1.5'
                }}>
                  {event.description || 'Event'}
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}