/* Panels.jsx — ADN dashboard with modern responsive UI */
'use client'
import { Activity, Brain, AlertTriangle, Lightbulb, CheckCircle2, AlertCircle, Clock } from './icons'

function useMergedData(data){
  const demo = {
    summary: {
      patientId: 'PAT-2024-1847',
      name: 'Marie Dubois, 65 ans',
      admission: '14:15 - Dyspnée aiguë',
      allergies: 'Pénicilline',
      antecedents: 'Hypertension (2019), Diabète Type 2 (2021), Fibrillation auriculaire (2023)',
      meds: 'Metformine 1000mg, Bisoprolol 5mg, Apixaban 5mg',
      vitals: 'TA: 145/92, FC: 110 irrég., SpO2: 89%, Temp: 37.8°C',
    },
    diagnostics: [
      {
        title: 'Embolie Pulmonaire',
        probability: 'Élevée',
        level: 'high',
        evidence: 'Dyspnée aiguë + ATCD TVP (alerte) + D-dimères ↑ + FA',
        extra: 'Score Wells: 7.5 (Risque élevé)',
        action: 'Angio-TDM thoracique urgente',
      },
      {
        title: 'Décompensation Cardiaque',
        probability: 'Moyenne',
        level: 'medium',
        evidence: 'FA connue + HTA + Dyspnée',
        counter: 'Absence de râles, BNP non élevé (dernière valeur)',
        action: 'ECG, Rx Thorax, NTproBNP',
      },
      {
        title: 'Pneumonie Atypique',
        probability: 'Faible',
        level: 'low',
        evidence: 'Fébricule + Dyspnée',
        counter: 'Absence de toux, CRP normale ce matin',
        action: 'Rx Thorax si autres causes exclues',
      },
    ],
    alerts: [
      {
        title: 'Antécédent de TVP Non Répertorié',
        detail:
          "Thrombose veineuse profonde documentée en 2018 (Note infirmière du 15/03/2018) absente de la liste des diagnostics actifs. Risque élevé d'embolie pulmonaire.",
        level: 'high',
      },
      {
        title: 'D-Dimères Élevés Non Signalés',
        detail:
          "Résultat laboratoire ce matin: D-Dimères à 2850 ng/mL (N < 500). Non mentionnés dans le rapport d'admission.",
        level: 'medium',
      },
    ],
    recommendations: [
      "PRIORITÉ URGENTE: Angio-TDM thoracique pour éliminer l'embolie pulmonaire (ATCD TVP + D-dimères élevés)",
      'Monitoring: Surveillance continue SpO2, installer O2 si < 92%',
      'Biologie: Gazométrie artérielle, NT-proBNP, Troponines',
      "Préparation: Prévenir l'équipe de réanimation si dégradation",
    ],
  }

  // normalize summary from either `summary` or nested `synthesis`
  const synthesis = data?.synthesis
  let normalizedSummary = null
  if (data?.summary && typeof data.summary === 'object') {
    normalizedSummary = data.summary
  } else if (synthesis && typeof synthesis === 'object') {
    try {
      const patientName = synthesis.patient?.name
        ? `${synthesis.patient.name}${synthesis.patient.age != null ? ', ' + synthesis.patient.age + ' ans' : ''}`
        : undefined
      const admission = synthesis.admission?.reason
      const allergies = Array.isArray(synthesis.allergies)
        ? synthesis.allergies.map(a => a?.substance).filter(Boolean).join(', ')
        : undefined
      const antecedents = Array.isArray(synthesis.antecedents)
        ? synthesis.antecedents
            .map(a => {
              const year = a?.year != null ? ` (${a.year})` : ''
              return `${a?.pathology ?? ''}${year}`
            })
            .filter(s => s && s.trim())
            .join(', ')
        : undefined
      const meds = Array.isArray(synthesis.current_medications)
        ? synthesis.current_medications
            .map(m => [m?.drug, m?.dosage].filter(Boolean).join(' '))
            .filter(Boolean)
            .join(', ')
        : undefined
      const vitals = synthesis.vital_signs
        ? [
            synthesis.vital_signs.blood_pressure
              ? `TA: ${synthesis.vital_signs.blood_pressure.systolic}/${synthesis.vital_signs.blood_pressure.diastolic}`
              : null,
            synthesis.vital_signs.heart_rate
              ? `FC: ${synthesis.vital_signs.heart_rate.value}${synthesis.vital_signs.heart_rate.rhythm ? ' ' + synthesis.vital_signs.heart_rate.rhythm : ''}`
              : null,
            synthesis.vital_signs.spo2 ? `SpO2: ${synthesis.vital_signs.spo2.value}%` : null,
            synthesis.vital_signs.temperature ? `Temp: ${synthesis.vital_signs.temperature.value}°C` : null,
          ]
            .filter(Boolean)
            .join(', ')
        : undefined

      normalizedSummary = {
        patientId: data?.patient_id || undefined,
        name: patientName,
        admission,
        allergies,
        antecedents,
        meds,
        vitals,
      }
    } catch {
      normalizedSummary = null
    }
  }

  // normalize diagnostics from either `diagnostics` or `differentials`
  let diagnostics = data?.diagnostics || data?.differentials || null
  if (Array.isArray(diagnostics) && diagnostics.length && diagnostics[0]?.pathology) {
    const levelMap = { 'Élevée': 'high', 'Elevée': 'high', 'Moyenne': 'medium', 'Faible': 'low', 'Haute': 'high' }
    diagnostics = diagnostics.map(d => {
      const probabilityLabel = d?.probability_label
      const level = levelMap[probabilityLabel] || 'medium'
      const evidenceText = Array.isArray(d?.evidence)
        ? d.evidence.map(ev => ev?.text).filter(Boolean).join(' • ')
        : undefined
      const action = Array.isArray(d?.suggested_actions)
        ? d.suggested_actions.map(a => a?.action).filter(Boolean).join(' | ')
        : undefined
      const extra = typeof d?.score === 'number' ? `Score: ${d.score}/10` : undefined
      return {
        title: d?.pathology,
        probability: probabilityLabel,
        level,
        evidence: evidenceText,
        extra,
        action,
      }
    })
  }

  // normalize alerts (severity/description → level/detail)
  let alerts = data?.alerts || null
  if (Array.isArray(alerts) && alerts.length && alerts[0]?.severity) {
    alerts = alerts.map(a => ({
      title: a?.title,
      detail: a?.description,
      level: a?.severity === 'critical' ? 'high' : 'medium',
      confidence: a?.confidence,
    }))
  }

  const recommendations = data?.recommendations || null

  return {
    summary: normalizedSummary ?? demo.summary,
    diagnostics: Array.isArray(diagnostics) && diagnostics.length ? diagnostics : demo.diagnostics,
    alerts: Array.isArray(alerts) && alerts.length ? alerts : demo.alerts,
    recommendations: Array.isArray(recommendations) && recommendations.length ? recommendations : demo.recommendations,
  }
}

export default function Panels({ data }) {
  const merged = useMergedData(data)

  return (
    <div className="panels-grid">
      {/* Synthèse Patient */}
      <section className="panel">
        <div className="title">
          <span>Synthèse Patient</span>
          <span className="small-badge">Agent Synthétiseur</span>
        </div>
        <div className="patient-card">
          {typeof merged.summary === 'object' ? (
            <div>
              {merged.summary.patientId && (
                <div style={{marginBottom:8}}><strong>ID:</strong> {merged.summary.patientId}</div>
              )}
              {merged.summary.name && (
                <div style={{marginBottom:8}}><strong>Patient:</strong> {merged.summary.name}</div>
              )}
              {merged.summary.admission && (
                <div style={{marginBottom:8}}><strong>Admission:</strong> {merged.summary.admission}</div>
              )}
              {merged.summary.allergies && (
                <div style={{marginBottom:8}}><strong>Allergies:</strong> {merged.summary.allergies}</div>
              )}
              {merged.summary.antecedents && (
                <div className="list-item" style={{marginTop:10}}>
                  <strong>Antécédents principaux:</strong>
                  <div style={{marginTop:6, color:'var(--muted)'}}>{merged.summary.antecedents}</div>
                </div>
              )}
              {merged.summary.meds && (
                <div className="list-item">
                  <strong>Médicaments actuels:</strong>
                  <div style={{marginTop:6, color:'var(--muted)'}}>{merged.summary.meds}</div>
                </div>
              )}
              {merged.summary.vitals && (
                <div className="list-item">
                  <strong>Signes vitaux:</strong>
                  <div style={{marginTop:6, color:'var(--muted)'}}>{merged.summary.vitals}</div>
                </div>
              )}
            </div>
          ) : (
            <pre style={{ whiteSpace: 'pre-wrap', margin: 0 }}>{String(merged.summary)}</pre>
          )}
        </div>
      </section>

      {/* Diagnostics Différentiels Suggérés */}
      <section className="panel">
        <div className="title">
          <span>Diagnostics Différentiels Suggérés</span>
          <span className="small-badge">Agent Expert</span>
        </div>
        <div>
          {Array.isArray(merged.diagnostics) ? (
            merged.diagnostics.map((dx, i) => (
              <div key={i} className="list-item diff-item">
                <div className="diff-left">
                  <div style={{fontWeight:600}}>{dx.title || dx.name || `Hypothèse ${i+1}`}</div>
                  {dx.evidence && (
                    <div style={{marginTop:6, color:'var(--muted)'}}>
                      <strong>Preuves Patient:</strong> {dx.evidence}
                    </div>
                  )}
                  {dx.extra && (
                    <div style={{marginTop:6, color:'var(--muted)'}}>{dx.extra}</div>
                  )}
                  {dx.counter && (
                    <div style={{marginTop:6, color:'var(--muted)'}}>
                      <strong>Contre:</strong> {dx.counter}
                    </div>
                  )}
                  {dx.action && (
                    <div style={{marginTop:6}}>
                      <strong>Action suggérée:</strong> {dx.action}
                    </div>
                  )}
                </div>
                <div>
                  <span className={`tag ${dx.level || 'medium'}`}>
                    {dx.probability ? `Probabilité ${dx.probability}` : 'Probabilité' }
                  </span>
                </div>
              </div>
            ))
          ) : (
            <div className="list-item">Aucune hypothèse disponible.</div>
          )}
        </div>
      </section>

      {/* Alertes Critiques Proactives */}
      <section className="panel">
        <div className="title">
          <span>Alertes Critiques Proactives</span>
          <span className="small-badge">Agent Critique</span>
        </div>
        <div>
          {Array.isArray(merged.alerts) ? (
            merged.alerts.map((a, i) => (
              <div key={i} className={`list-item ${a.level === 'high' ? 'alert-high' : a.level === 'medium' ? 'alert-medium' : ''}`}>
                <div style={{fontWeight:600, marginBottom:6}}>{a.title || `Alerte ${i+1}`}</div>
                <div style={{color:'var(--muted)'}}>{a.detail || a.text || ''}</div>
              </div>
            ))
          ) : (
            <div className="list-item">Aucune alerte détectée.</div>
          )}
        </div>
      </section>

      {/* Recommandations Immédiates */}
      <section className="panel">
        <div className="title">
          <span>Recommandations Immédiates</span>
        </div>
        {Array.isArray(merged.recommendations) ? (
          <ul className="reco-list">
            {merged.recommendations.map((r, i) => (
              <li key={i} className="list-item">
                <strong style={{marginRight:8}}>{i + 1}.</strong>
                {typeof r === 'object' && r !== null ? (
                  <span>
                    {[
                      r.priority != null ? `#${r.priority}` : null,
                      r.category || null,
                      r.title || null,
                    ].filter(Boolean).join(' • ')}
                    {r.description ? ` — ${r.description}` : ''}
                    {r.expected_delay ? ` (${r.expected_delay})` : ''}
                  </span>
                ) : (
                  String(r)
                )}
              </li>
            ))}
          </ul>
        ) : (
          <div className="list-item">Aucune recommandation disponible.</div>
        )}
      </section>
    </div>
  )
}
