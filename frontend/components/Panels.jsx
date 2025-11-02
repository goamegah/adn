/* Panels.jsx - Compatible avec getAgentOutputs et données backend */
'use client'
import { Activity, Brain, AlertTriangle, Lightbulb, CheckCircle2, AlertCircle, Clock, Shield, Target, TrendingUp } from './icons'

// Composant: Synthèse Patient (Agent Collecteur)
export const PatientSynthesis = ({ data }) => {
  console.log('PatientSynthesis data:', data)
  
  if (!data) {
    return (
      <div className="bg-slate-800/50 backdrop-blur border border-slate-700 rounded-xl p-6">
        <div className="flex items-center gap-2 mb-4">
          <Activity className="w-5 h-5 text-blue-400" />
          <h2 className="text-lg font-semibold">Synthèse Patient</h2>
          <span className="text-xs text-slate-400 ml-auto">Agent Collecteur</span>
        </div>
        <p className="text-slate-400 text-sm">Aucune donnée patient disponible</p>
      </div>
    )
  }
  
  // Extraire les données patient
  const patientData = data.patient || data
  const admission = patientData.admission || {}
  const labs = patientData.labs || []
  const cultures = patientData.cultures || []
  const medications = patientData.medications || []
  const diagnoses = patientData.diagnoses || []
  const vitals = patientData.vitals || {}
  
  return (
    <div className="bg-gradient-to-br from-slate-800/80 to-slate-800/50 backdrop-blur border-2 border-slate-600 rounded-2xl p-6 shadow-2xl">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6 pb-4 border-b-2 border-slate-700">
        <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl flex items-center justify-center shadow-lg">
          <Activity className="w-7 h-7 text-white" />
        </div>
        <div className="flex-1">
          <h2 className="text-xl font-bold text-white">Synthèse Patient</h2>
          <p className="text-sm text-blue-300 font-medium">Agent Collecteur</p>
        </div>
        <div className="px-4 py-2 bg-blue-500/20 border border-blue-400/50 rounded-lg">
          <span className="text-blue-300 text-xs font-semibold">ACTIF</span>
        </div>
      </div>
      
      {/* Contenu */}
      <div className="space-y-5">
        {/* Info patient */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {patientData.id && (
            <div className="bg-slate-900/50 rounded-xl p-4 border border-slate-700">
              <p className="text-slate-400 text-xs font-semibold uppercase tracking-wider mb-2">Patient ID</p>
              <p className="text-white font-bold text-lg">
                #{patientData.id}
                {patientData.age && <span className="text-slate-300 font-normal text-base ml-2">· {patientData.age} ans</span>}
                {patientData.sex && <span className="text-slate-400 font-normal text-sm ml-2">({patientData.sex})</span>}
              </p>
            </div>
          )}
          
          {admission.chief_complaint && (
            <div className="bg-slate-900/50 rounded-xl p-4 border border-slate-700">
              <p className="text-slate-400 text-xs font-semibold uppercase tracking-wider mb-2">Motif d'admission</p>
              <p className="text-white font-semibold text-base">{admission.chief_complaint}</p>
              {admission.type && <p className="text-slate-400 text-xs mt-1">{admission.type}</p>}
            </div>
          )}
        </div>

        {/* Médicaments */}
        {medications.length > 0 && (
          <div className="bg-slate-900/30 rounded-xl p-5 border border-slate-700">
            <div className="flex items-center gap-2 mb-3">
              <Target className="w-5 h-5 text-green-400" />
              <p className="text-slate-300 text-sm font-bold uppercase tracking-wider">Médicaments actuels</p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
              {medications.slice(0, 6).map((med, i) => (
                <div key={i} className="bg-slate-800/50 rounded-lg p-3 border border-slate-700">
                  <p className="text-white font-semibold text-sm">{med.drug}</p>
                  {med.dose && <p className="text-slate-400 text-xs mt-1">{med.dose} {med.route && `(${med.route})`}</p>}
                </div>
              ))}
            </div>
            {medications.length > 6 && (
              <p className="text-slate-400 text-xs mt-2">+ {medications.length - 6} autres médicaments</p>
            )}
          </div>
        )}

        {/* Cultures positives */}
        {cultures.filter(c => c.isPositive).length > 0 && (
          <div className="bg-red-500/10 border-l-4 border-red-500 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-2">
              <AlertCircle className="w-5 h-5 text-red-400" />
              <p className="text-red-300 text-sm font-bold uppercase tracking-wider">⚠️ Cultures Positives</p>
            </div>
            <div className="space-y-2">
              {cultures.filter(c => c.isPositive).map((culture, i) => (
                <div key={i} className="bg-red-900/20 rounded-lg p-3">
                  <p className="text-red-200 font-semibold text-sm">{culture.organism}</p>
                  <p className="text-red-300/70 text-xs">{culture.spec_type}</p>
                  {culture.antibiotic && (
                    <p className="text-xs mt-1">
                      <span className="text-slate-400">{culture.antibiotic}: </span>
                      <span className={`font-semibold ${
                        culture.isSensitive ? 'text-green-300' :
                        culture.isResistant ? 'text-red-300' :
                        'text-yellow-300'
                      }`}>
                        {culture.interpretation === 'S' ? 'Sensible' :
                         culture.interpretation === 'R' ? 'Résistant' :
                         'Intermédiaire'}
                      </span>
                    </p>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Diagnostics ICD */}
        {diagnoses.length > 0 && (
          <div className="bg-slate-900/30 rounded-xl p-5 border border-slate-700">
            <div className="flex items-center gap-2 mb-3">
              <Shield className="w-5 h-5 text-slate-400" />
              <p className="text-slate-300 text-sm font-bold uppercase tracking-wider">Diagnostics (ICD-9)</p>
            </div>
            <div className="space-y-1">
              {diagnoses.slice(0, 5).map((diag, i) => (
                <div key={i} className="flex items-center gap-2 text-slate-200">
                  <div className="w-2 h-2 bg-blue-400 rounded-full"></div>
                  <span className="text-sm font-medium">Code {diag.icd9_code}</span>
                </div>
              ))}
              {diagnoses.length > 5 && (
                <p className="text-slate-400 text-xs mt-2">+ {diagnoses.length - 5} autres diagnostics</p>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

// Composant: Diagnostics Différentiels (Agent Expert)
export const DiagnosticDifferentials = ({ data }) => {
  console.log('DiagnosticDifferentials data:', data)
  
  if (!data || !data.differential_diagnoses || data.differential_diagnoses.length === 0) {
    return (
      <div className="bg-slate-800/50 backdrop-blur border border-slate-700 rounded-xl p-6">
        <div className="flex items-center gap-2 mb-4">
          <Brain className="w-5 h-5 text-purple-400" />
          <h2 className="text-lg font-semibold">Diagnostics Différentiels</h2>
          <span className="text-xs text-slate-400 ml-auto">Agent Expert</span>
        </div>
        <p className="text-slate-400 text-sm">Aucun diagnostic différentiel disponible</p>
      </div>
    )
  }
  
  const diagnoses = data.differential_diagnoses || []
  
  return (
    <div className="bg-gradient-to-br from-slate-800/80 to-slate-800/50 backdrop-blur border-2 border-slate-600 rounded-2xl p-6 shadow-2xl">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6 pb-4 border-b-2 border-slate-700">
        <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-purple-600 rounded-xl flex items-center justify-center shadow-lg">
          <Brain className="w-7 h-7 text-white" />
        </div>
        <div className="flex-1">
          <h2 className="text-xl font-bold text-white">Diagnostics Différentiels</h2>
          <p className="text-sm text-purple-300 font-medium">Agent Expert</p>
        </div>
        <div className="px-4 py-2 bg-purple-500/20 border border-purple-400/50 rounded-lg">
          <span className="text-purple-300 text-xs font-semibold">{diagnoses.length} HYPOTHÈSES</span>
        </div>
      </div>

      {/* Liste des diagnostics */}
      <div className="space-y-4">
        {diagnoses.map((diag, i) => {
          const prob = diag.probability || 'MEDIUM'
          const colors = {
            'VERY_HIGH': { bg: 'bg-red-500/10', border: 'border-red-500/50', text: 'text-red-300', badge: 'bg-red-500/30 border-red-400 text-red-200' },
            'HIGH': { bg: 'bg-red-500/10', border: 'border-red-500/50', text: 'text-red-300', badge: 'bg-red-500/30 border-red-400 text-red-200' },
            'MEDIUM': { bg: 'bg-yellow-500/10', border: 'border-yellow-500/50', text: 'text-yellow-300', badge: 'bg-yellow-500/30 border-yellow-400 text-yellow-200' },
            'LOW': { bg: 'bg-green-500/10', border: 'border-green-500/50', text: 'text-green-300', badge: 'bg-green-500/30 border-green-400 text-green-200' }
          }
          const style = colors[prob] || colors['MEDIUM']
          
          return (
            <div
              key={i}
              className={`${style.bg} border-l-4 ${style.border} rounded-xl p-5 hover:scale-[1.02] transition-transform`}
            >
              {/* Header */}
              <div className="flex items-start justify-between mb-4 gap-3">
                <h3 className="font-bold text-white text-lg flex-1">{diag.diagnosis}</h3>
                <span className={`px-4 py-2 rounded-lg text-xs font-bold uppercase border-2 ${style.badge} whitespace-nowrap`}>
                  {prob}
                </span>
              </div>

              {/* Preuves */}
              {diag.supporting_evidence && diag.supporting_evidence.length > 0 && (
                <div className="mb-4">
                  <p className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">✓ Preuves</p>
                  <div className="space-y-2">
                    {diag.supporting_evidence.map((ev, j) => (
                      <div key={j} className="flex items-start gap-2 bg-slate-800/30 rounded-lg p-3">
                        <CheckCircle2 className="w-4 h-4 text-blue-400 flex-shrink-0 mt-0.5" />
                        <div className="flex-1">
                          <p className="text-sm text-slate-200 font-medium">{ev.statement}</p>
                          <p className="text-xs text-slate-500 mt-1">Source: {ev.source}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Contre-preuves */}
              {diag.contradicting_evidence && diag.contradicting_evidence.length > 0 && (
                <div className="mb-4">
                  <p className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">✗ Contre-indications</p>
                  <div className="space-y-2">
                    {diag.contradicting_evidence.map((ev, j) => (
                      <div key={j} className="flex items-start gap-2 bg-slate-800/30 rounded-lg p-3">
                        <AlertCircle className="w-4 h-4 text-red-400 flex-shrink-0 mt-0.5" />
                        <div className="flex-1">
                          <p className="text-sm text-slate-300">{ev.statement}</p>
                          <p className="text-xs text-slate-500 mt-1">Source: {ev.source}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Confiance */}
              <div className="pt-3 border-t border-slate-700 flex items-center gap-2">
                <span className="text-xs text-slate-400 font-semibold">Confiance:</span>
                <div className="flex-1 bg-slate-800 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full transition-all ${
                      diag.confidence === 'HIGH' ? 'bg-green-500 w-4/5' :
                      diag.confidence === 'MEDIUM' ? 'bg-yellow-500 w-3/5' :
                      'bg-red-500 w-2/5'
                    }`}
                  />
                </div>
                <span className="text-xs text-slate-300 font-bold">{diag.confidence}</span>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

// Composant: Alertes Critiques (Agent Synthétiseur)
export const CriticalAlerts = ({ data }) => {
  console.log('CriticalAlerts data:', data)
  
  if (!data) {
    return (
      <div className="bg-slate-800/50 backdrop-blur border border-slate-700 rounded-xl p-6">
        <div className="flex items-center gap-2 mb-4">
          <AlertTriangle className="w-5 h-5 text-yellow-400" />
          <h2 className="text-lg font-semibold">Alertes Critiques</h2>
          <span className="text-xs text-slate-400 ml-auto">Agent Synthétiseur</span>
        </div>
        <p className="text-slate-400 text-sm">Agent Synthétiseur non disponible</p>
      </div>
    )
  }
  
  const alerts = data.critical_alerts || []
  
  // Si pas d'alertes, afficher un message positif
  if (alerts.length === 0) {
    return (
      <div className="bg-gradient-to-br from-slate-800/80 to-slate-800/50 backdrop-blur border-2 border-green-600 rounded-2xl p-6 shadow-2xl">
        <div className="flex items-center gap-3 mb-4 pb-4 border-b-2 border-green-700">
          <div className="w-12 h-12 bg-gradient-to-br from-green-500 to-green-600 rounded-xl flex items-center justify-center shadow-lg">
            <CheckCircle2 className="w-7 h-7 text-white" />
          </div>
          <div className="flex-1">
            <h2 className="text-xl font-bold text-white">Alertes Critiques</h2>
            <p className="text-sm text-green-300 font-medium">Agent Synthétiseur</p>
          </div>
          <div className="px-4 py-2 bg-green-500/20 border border-green-400/50 rounded-lg">
            <span className="text-green-300 text-xs font-semibold">0 ALERTE</span>
          </div>
        </div>
        <div className="flex items-center gap-3 p-4 bg-green-500/10 border border-green-500/50 rounded-xl">
          <CheckCircle2 className="w-6 h-6 text-green-400" />
          <p className="text-green-200 text-sm font-medium">✅ Aucune alerte critique détectée</p>
        </div>
      </div>
    )
  }
  
  return (
    <div className="bg-gradient-to-br from-slate-800/80 to-slate-800/50 backdrop-blur border-2 border-red-600 rounded-2xl p-6 shadow-2xl shadow-red-900/30">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6 pb-4 border-b-2 border-red-700">
        <div className="w-12 h-12 bg-gradient-to-br from-red-500 to-red-600 rounded-xl flex items-center justify-center shadow-lg animate-pulse">
          <AlertTriangle className="w-7 h-7 text-white" />
        </div>
        <div className="flex-1">
          <h2 className="text-xl font-bold text-white">Alertes Critiques</h2>
          <p className="text-sm text-red-300 font-medium">Agent Synthétiseur</p>
        </div>
        <div className="px-4 py-2 bg-red-500/30 border-2 border-red-400 rounded-lg animate-pulse">
          <span className="text-red-200 text-xs font-bold">{alerts.length} ALERTES</span>
        </div>
      </div>

      {/* Liste des alertes */}
      <div className="space-y-3">
        {alerts.map((alert, i) => {
          const isCritical = alert.severity === 'CRITICAL' || alert.isHigh
          
          return (
            <div
              key={i}
              className={`rounded-xl p-5 border-l-4 ${
                isCritical
                  ? 'bg-red-500/20 border-red-500 shadow-lg shadow-red-900/20'
                  : 'bg-yellow-500/20 border-yellow-500 shadow-lg shadow-yellow-900/20'
              }`}
            >
              <div className="flex items-start gap-4">
                <div className={`flex-shrink-0 w-10 h-10 rounded-lg flex items-center justify-center ${
                  isCritical ? 'bg-red-500/30' : 'bg-yellow-500/30'
                }`}>
                  {isCritical ? (
                    <AlertCircle className="w-6 h-6 text-red-300" />
                  ) : (
                    <AlertTriangle className="w-6 h-6 text-yellow-300" />
                  )}
                </div>
                
                <div className="flex-1">
                  <p className={`font-bold text-base mb-2 uppercase ${
                    isCritical ? 'text-red-200' : 'text-yellow-200'
                  }`}>
                    {alert.type}
                  </p>
                  <p className="text-sm text-slate-200 leading-relaxed mb-3">
                    {alert.finding}
                  </p>
                  
                  {alert.action_required && (
                    <div className="mt-3 pt-3 border-t border-slate-700">
                      <p className="text-xs font-bold uppercase text-blue-300 mb-2">→ Action requise</p>
                      <p className="text-sm text-blue-200">{alert.action_required}</p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

// Composant: Plan d'Action (Agent Expert)
export const ActionPlan = ({ data }) => {
  console.log('ActionPlan data:', data)
  
  if (!data || !data.action_plan) {
    return null
  }
  
  const plan = data.action_plan
  const allActions = [
    ...(plan.immediate_actions || []),
    ...(plan.urgent_actions || []),
    ...(plan.diagnostic_workup || [])
  ]
  
  if (allActions.length === 0) return null
  
  return (
    <div className="bg-gradient-to-br from-slate-800/80 to-slate-800/50 backdrop-blur border-2 border-slate-600 rounded-2xl p-6 shadow-2xl">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6 pb-4 border-b-2 border-slate-700">
        <div className="w-12 h-12 bg-gradient-to-br from-yellow-500 to-yellow-600 rounded-xl flex items-center justify-center shadow-lg">
          <Lightbulb className="w-7 h-7 text-white" />
        </div>
        <div className="flex-1">
          <h2 className="text-xl font-bold text-white">Plan d'Action</h2>
          <p className="text-sm text-yellow-300 font-medium">Agent Expert</p>
        </div>
        <div className="px-4 py-2 bg-yellow-500/20 border border-yellow-400/50 rounded-lg">
          <span className="text-yellow-300 text-xs font-semibold">{allActions.length} ACTIONS</span>
        </div>
      </div>

      {/* Timeline des actions */}
      <div className="space-y-4">
        {allActions.map((action, i) => {
          const priority = action.priority || 'URGENT'
          const priorityColors = {
            'IMMEDIATE': { bg: 'bg-red-500', text: 'text-red-200', border: 'border-red-500', ring: 'ring-red-500/30' },
            'URGENT': { bg: 'bg-yellow-500', text: 'text-yellow-900', border: 'border-yellow-500', ring: 'ring-yellow-500/30' },
            'ROUTINE': { bg: 'bg-blue-500', text: 'text-blue-200', border: 'border-blue-500', ring: 'ring-blue-500/30' }
          }
          const colors = priorityColors[priority] || priorityColors['URGENT']
          
          return (
            <div key={i} className="flex gap-4">
              <div className="flex flex-col items-center">
                <div className={`w-10 h-10 rounded-full ${colors.bg} flex items-center justify-center text-sm font-bold ${colors.text} shadow-lg ring-4 ${colors.ring}`}>
                  {i + 1}
                </div>
                {i < allActions.length - 1 && (
                  <div className="w-0.5 flex-1 bg-gradient-to-b from-slate-600 to-transparent mt-2"></div>
                )}
              </div>
              
              <div className={`flex-1 bg-slate-800/50 border-2 ${colors.border} rounded-xl p-4 hover:scale-[1.02] transition-transform`}>
                <p className={`text-xs font-bold uppercase tracking-wider mb-2 ${
                  priority === 'IMMEDIATE' ? 'text-red-300' : 'text-slate-400'
                }`}>
                  {priority} {action.time_window && `· ${action.time_window}`}
                </p>
                <p className="text-base text-white font-semibold mb-2">{action.action}</p>
                {action.rationale && (
                  <p className="text-sm text-slate-300 leading-relaxed">{action.rationale}</p>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

// Export par défaut - Affiche tous les panels
export default function Panels({ data }) {
  console.log('=== Panels data received ===', data)
  
  if (!data) {
    return (
      <div className="text-center text-slate-400 py-12">
        <p>Aucune donnée disponible</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Agent Collecteur - Données patient */}
      {data.patient && <PatientSynthesis data={data} />}
      
      {/* Agent Synthétiseur - Alertes */}
      {data.synthesis && <CriticalAlerts data={data.synthesis} />}
      
      {/* Agent Expert - Diagnostics */}
      {data.expert && data.expert.differential_diagnoses && data.expert.differential_diagnoses.length > 0 && (
        <DiagnosticDifferentials data={data.expert} />
      )}
      
      {/* Agent Expert - Plan d'action */}
      {data.expert && data.expert.action_plan && (
        <ActionPlan data={data.expert} />
      )}
    </div>
  )
}