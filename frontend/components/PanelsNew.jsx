/* Panels.jsx — ADN dashboard with modern responsive UI */
'use client'
import { Activity, Brain, AlertTriangle, Lightbulb, CheckCircle2, AlertCircle, Clock } from './icons'

// Badge de probabilité
const ProbabilityBadge = ({ level }) => {
  const colors = {
    'Élevée': 'bg-red-500/20 text-red-300 border-red-500/50',
    'Elevée': 'bg-red-500/20 text-red-300 border-red-500/50',
    'Moyenne': 'bg-yellow-500/20 text-yellow-300 border-yellow-500/50',
    'Faible': 'bg-green-500/20 text-green-300 border-green-500/50',
    'high': 'bg-red-500/20 text-red-300 border-red-500/50',
    'medium': 'bg-yellow-500/20 text-yellow-300 border-yellow-500/50',
    'low': 'bg-green-500/20 text-green-300 border-green-500/50'
  }
  return (
    <span className={`px-3 py-1 rounded-full text-xs font-semibold border ${colors[level] || colors['medium']}`}>
      {level}
    </span>
  )
}

// Composant: Synthèse Patient
export const PatientSynthesis = ({ data }) => {
  if (!data) return null
  
  const summary = typeof data === 'object' ? data : {}
  const patient = summary.patient || {}
  const admission = summary.admission || {}
  const allergies = summary.allergies || []
  const antecedents = summary.antecedents || []
  const meds = summary.current_medications || []
  const vitals = summary.vital_signs || {}
  
  return (
    <div className="bg-slate-800/50 backdrop-blur border border-slate-700 rounded-xl p-4 md:p-6 animate-in">
      <div className="flex items-center gap-2 mb-4">
        <Activity className="w-5 h-5 text-blue-400" />
        <h2 className="text-base md:text-lg font-semibold">Synthèse Patient</h2>
        <span className="text-xs text-slate-400 ml-auto">Agent Synthétiseur</span>
      </div>
      
      <div className="space-y-4">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {(patient.name || summary.name) && (
            <div>
              <p className="text-slate-400 text-sm">Patient:</p>
              <p className="font-semibold">{patient.name || summary.name}{patient.age ? `, ${patient.age} ans` : summary.age ? `, ${summary.age}` : ''}</p>
            </div>
          )}
          {(admission.reason || summary.admission) && (
            <div>
              <p className="text-slate-400 text-sm">Admission:</p>
              <p className="font-semibold">{admission.reason || summary.admission}</p>
            </div>
          )}
        </div>
        
        {(allergies.length > 0 || summary.allergies) && (
          <div>
            <p className="text-slate-400 text-sm">Allergies:</p>
            <p className="font-semibold text-red-400">
              {Array.isArray(allergies) 
                ? allergies.map(a => a.substance || a).join(', ')
                : summary.allergies}
            </p>
          </div>
        )}

        {(antecedents.length > 0 || summary.antecedents) && (
          <div>
            <p className="text-slate-400 text-sm mb-2">ANTÉCÉDENTS</p>
            <div className="space-y-1">
              {Array.isArray(antecedents) && antecedents.length > 0 ? (
                antecedents.map((ant, i) => (
                  <p key={i} className="text-sm text-slate-300">
                    {ant.pathology || ant} {ant.year && `(${ant.year})`}
                  </p>
                ))
              ) : (
                <p className="text-sm text-slate-300">{summary.antecedents}</p>
              )}
            </div>
          </div>
        )}

        {(meds.length > 0 || summary.meds) && (
          <div>
            <p className="text-slate-400 text-sm mb-2">MÉDICAMENTS</p>
            <div className="space-y-1">
              {Array.isArray(meds) && meds.length > 0 ? (
                meds.map((med, i) => (
                  <p key={i} className="text-sm text-slate-300">
                    {med.drug || med} {med.dosage || ''}
                  </p>
                ))
              ) : (
                <p className="text-sm text-slate-300">{summary.meds}</p>
              )}
            </div>
          </div>
        )}

        {(vitals.blood_pressure || summary.vitals) && (
          <div className="bg-slate-900/50 rounded-lg p-3">
            <p className="text-slate-400 text-sm">SIGNES VITAUX</p>
            <div className="grid grid-cols-2 gap-2 mt-2 text-sm">
              {vitals.blood_pressure ? (
                <>
                  <div>TA: {vitals.blood_pressure.systolic}/{vitals.blood_pressure.diastolic}</div>
                  <div>FC: {vitals.heart_rate?.value} {vitals.heart_rate?.rhythm && `(${vitals.heart_rate.rhythm})`}</div>
                  <div>SpO2: {vitals.spo2?.value}%</div>
                  <div>Temp: {vitals.temperature?.value}°C</div>
                </>
              ) : (
                <div className="col-span-2">{summary.vitals}</div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

// Composant: Diagnostics Différentiels
export const DiagnosticDifferentials = ({ data }) => {
  if (!data || data.length === 0) return null
  
  return (
    <div className="bg-slate-800/50 backdrop-blur border border-slate-700 rounded-xl p-4 md:p-6 animate-in">
      <div className="flex items-center gap-2 mb-4">
        <Brain className="w-5 h-5 text-purple-400" />
        <h2 className="text-base md:text-lg font-semibold">Diagnostics Différentiels</h2>
        <span className="text-xs text-slate-400 ml-auto">Agent Expert</span>
      </div>

      <div className="space-y-4">
        {data.map((diff, i) => {
          const title = diff.pathology || diff.title || diff.name || `Hypothèse ${i+1}`
          const probability = diff.probability_label || diff.probability
          const level = diff.level || (probability === 'Élevée' || probability === 'Elevée' ? 'high' : probability === 'Moyenne' ? 'medium' : 'low')
          const evidence = diff.evidence || []
          const actions = diff.suggested_actions || []
          const score = diff.score
          const extraInfo = diff.extra
          
          return (
            <div
              key={i}
              className="bg-slate-900/50 rounded-lg p-4 border border-slate-700 hover:border-slate-600 transition-colors"
            >
              <div className="flex items-start justify-between mb-3 gap-2">
                <h3 className="font-semibold text-white">{title}</h3>
                <ProbabilityBadge level={probability || level} />
              </div>

              {(evidence.length > 0 || diff.evidenceText) && (
                <div className="mb-3">
                  <p className="text-xs text-slate-400 mb-2">Preuves:</p>
                  <div className="space-y-1">
                    {Array.isArray(evidence) && evidence.length > 0 ? (
                      evidence.map((ev, j) => (
                        <div key={j} className="flex items-start gap-2">
                          <CheckCircle2 className="w-3 h-3 text-blue-400 flex-shrink-0 mt-0.5" />
                          <p className="text-xs text-slate-300">
                            {ev.text || ev}
                            {ev.source && <span className="text-slate-500 ml-1">({ev.source})</span>}
                          </p>
                        </div>
                      ))
                    ) : (
                      <p className="text-xs text-slate-300">{diff.evidenceText}</p>
                    )}
                  </div>
                </div>
              )}

              {diff.counter && (
                <div className="mb-3 text-xs text-slate-400">
                  <strong>Contre:</strong> {diff.counter}
                </div>
              )}

              {extraInfo && (
                <div className="mb-3 text-xs text-slate-400">{extraInfo}</div>
              )}

              {(actions.length > 0 || diff.action) && (
                <div className="pt-3 border-t border-slate-700">
                  <p className="text-xs text-slate-400">Actions suggérées:</p>
                  <div className="mt-1 space-y-1">
                    {Array.isArray(actions) && actions.length > 0 ? (
                      actions.map((action, k) => (
                        <p key={k} className="text-sm text-blue-300 font-medium">
                          {action.action || action}
                        </p>
                      ))
                    ) : (
                      <p className="text-sm text-blue-300 font-medium">{diff.action}</p>
                    )}
                  </div>
                </div>
              )}

              {score && (
                <div className="mt-3 flex items-center gap-2">
                  <div className="flex-1 bg-slate-800 rounded-full h-2">
                    <div
                      className="bg-gradient-to-r from-green-500 via-yellow-500 to-red-500 h-2 rounded-full transition-all duration-1000"
                      style={{ width: `${(score / 10) * 100}%` }}
                    />
                  </div>
                  <span className="text-xs text-slate-400">Score: {score}/10</span>
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}

// Composant: Alertes Critiques
export const CriticalAlerts = ({ data }) => {
  if (!data || data.length === 0) return null
  
  return (
    <div className="bg-slate-800/50 backdrop-blur border border-slate-700 rounded-xl p-4 md:p-6 animate-in">
      <div className="flex items-center gap-2 mb-4">
        <AlertTriangle className="w-5 h-5 text-yellow-400" />
        <h2 className="text-base md:text-lg font-semibold">Alertes Critiques</h2>
        <span className="text-xs text-slate-400 ml-auto">Agent Critique</span>
      </div>

      <div className="space-y-3">
        {data.map((alert, i) => {
          const isCritical = alert.severity === 'critical' || alert.level === 'high'
          
          return (
            <div
              key={i}
              className={`rounded-lg p-4 border-l-4 ${
                isCritical
                  ? 'bg-red-500/10 border-red-500'
                  : 'bg-yellow-500/10 border-yellow-500'
              }`}
            >
              <div className="flex items-start gap-3">
                {isCritical ? (
                  <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
                ) : (
                  <AlertTriangle className="w-5 h-5 text-yellow-400 flex-shrink-0 mt-0.5" />
                )}
                <div className="flex-1">
                  <p className="font-semibold text-sm mb-1">{alert.title}</p>
                  <p className="text-xs text-slate-300 leading-relaxed">{alert.description || alert.detail}</p>
                  {alert.confidence && (
                    <div className="mt-2 flex items-center gap-2">
                      <span className="text-xs text-slate-500">
                        Confiance: {(alert.confidence * 100).toFixed(0)}%
                      </span>
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

// Composant: Recommandations
export const ImmediateRecommendations = ({ data }) => {
  if (!data || data.length === 0) return null
  
  return (
    <div className="bg-slate-800/50 backdrop-blur border border-slate-700 rounded-xl p-4 md:p-6 animate-in">
      <div className="flex items-center gap-2 mb-4">
        <Lightbulb className="w-5 h-5 text-yellow-400" />
        <h2 className="text-base md:text-lg font-semibold">Recommandations Immédiates</h2>
      </div>

      <div className="space-y-3">
        {data.map((rec, i) => {
          const priority = rec.priority || i + 1
          const isString = typeof rec === 'string'
          
          return (
            <div key={i} className="flex items-start gap-3">
              <div className={`flex-shrink-0 w-7 h-7 rounded-full flex items-center justify-center text-sm font-bold ${
                priority === 1 ? 'bg-red-500 text-white' :
                priority === 2 ? 'bg-yellow-500 text-slate-900' :
                priority === 3 ? 'bg-blue-500 text-white' :
                'bg-slate-600 text-white'
              }`}>
                {priority}
              </div>
              <div className="flex-1">
                {isString ? (
                  <p className="text-sm text-slate-200">{rec}</p>
                ) : (
                  <>
                    {rec.category && (
                      <p className={`text-xs font-semibold mb-1 ${
                        priority === 1 ? 'text-red-400' : 'text-slate-400'
                      }`}>
                        {rec.category}
                      </p>
                    )}
                    <p className="text-sm text-slate-200 font-medium">{rec.title}</p>
                    {rec.description && (
                      <p className="text-xs text-slate-400 mt-1">{rec.description}</p>
                    )}
                    {rec.expected_delay && (
                      <div className="flex items-center gap-1 mt-1">
                        <Clock className="w-3 h-3 text-slate-500" />
                        <span className="text-xs text-slate-500">{rec.expected_delay}</span>
                      </div>
                    )}
                  </>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

// Export par défaut pour compatibilité
export default function Panels({ data }) {
  if (!data) return null

  return (
    <>
      <PatientSynthesis data={data.patient_summary || data.summary || data.synthesis} />
      <DiagnosticDifferentials data={data.differentials || data.diagnostics} />
      <CriticalAlerts data={data.alerts} />
      <ImmediateRecommendations data={data.recommendations} />
    </>
  )
}
