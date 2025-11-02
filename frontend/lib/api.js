// lib/api.js - Client API pour le backend clinical

const API_BASE_URL = 'https://adn-app-759263279097.europe-west1.run.app'

/**
 * Créer une nouvelle session
 * @returns {Promise<Object>} Les données de la session créée
 */
export async function startSession() {
  const response = await fetch(`${API_BASE_URL}/start_session`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      user_id: "user_backend"
    }),
  })

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`)
  }

  return await response.json()
}

/**
 * Analyser un patient
 * @param {number|null} subjectId - L'ID du patient (MIMIC-III)
 * @param {string|null} texteMedical - Texte médical libre
 * @returns {Promise<Object>} Les résultats de l'analyse
 */
export async function analyze(subjectId = null, texteMedical = null) {
  const payload = {}
  
  if (subjectId) {
    payload.subject_id = parseInt(subjectId)
  }
  
  if (texteMedical) {
    payload.texte_medical = texteMedical
  }

  if (!subjectId && !texteMedical) {
    throw new Error('Vous devez fournir soit subject_id soit texte_medical')
  }

  const response = await fetch(`${API_BASE_URL}/analyse`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`)
  }

  return await response.json()
}

/**
 * Vérifier l'état du backend
 * @returns {Promise<Object>} Message de statut
 */
export async function healthCheck() {
  const response = await fetch(`${API_BASE_URL}/`, {
    method: 'GET',
  })

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`)
  }

  return await response.json()
}

/**
 * Envoyer un message à l'agent clinique
 * @param {string} message - Le message de l'utilisateur
 * @returns {Promise<Object>} La réponse de l'agent
 */
export async function sendMessage(message) {
  const response = await fetch(`${API_BASE_URL}/send_message`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ 
      query: message,
      user_id: "user_backend",
      session_id: "session_api"
    }),
  })

  if (!response.ok) {
    const errorText = await response.text()
    throw new Error(`HTTP ${response.status}: ${errorText}`)
  }

  const data = await response.json()
  
  // Si data.response existe (texte direct du backend), le retourner
  if (data.response) {
    return data.response
  }
  
  // Si data.output existe, le retourner
  if (data.output !== undefined) {
    return data.output
  }
  
  // Sinon retourner data directement
  return data
}

/**
 * Récupérer l'état de la session
 * @param {string} userId - ID de l'utilisateur (optionnel)
 * @param {string} sessionId - ID de session (optionnel)
 * @returns {Promise<Object>} L'état de la session
 */
export async function getState(userId = null, sessionId = null) {
  const payload = {}
  
  if (userId) payload.user_id = userId
  if (sessionId) payload.session_id = sessionId
  
  const response = await fetch(`${API_BASE_URL}/get_state`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    const errorText = await response.text()
    throw new Error(`HTTP ${response.status}: ${errorText}`)
  }

  return await response.json()
}

/**
 * Récupérer les outputs des agents (collecteur, synthétiseur, expert)
 * Retourne une structure propre et détaillée de tous les éléments
 * @param {string} userId - ID de l'utilisateur (optionnel)
 * @param {string} sessionId - ID de session (optionnel)
 * @returns {Promise<Object>} Les outputs structurés des agents
 */
export async function getAgentOutputs(userId = null, sessionId = null) {
  const payload = {}
  
  if (userId) payload.user_id = userId
  if (sessionId) payload.session_id = sessionId
  
  const response = await fetch(`${API_BASE_URL}/get_agent_outputs`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    const errorText = await response.text()
    throw new Error(`HTTP ${response.status}: ${errorText}`)
  }

  const data = await response.json()
  
  // Extraire et structurer les données
  return extractAndStructureOutputs(data)
}

/**
 * Extrait et structure proprement les outputs des 3 agents
 */
function extractAndStructureOutputs(rawData) {
  let { donnees_patient, synthese_clinique, validation_expert } = rawData.agent_outputs || {}
  
  // Parser donnees_patient si c'est une string JSON
  if (typeof donnees_patient === 'string') {
    try {
      const jsonMatch = donnees_patient.match(/```json\n([\s\S]*?)\n```/)
      if (jsonMatch) {
        donnees_patient = JSON.parse(jsonMatch[1])
      } else {
        donnees_patient = JSON.parse(donnees_patient)
      }
    } catch (e) {
      console.error('Erreur parsing donnees_patient:', e)
      donnees_patient = null
    }
  }
  
  const patient = donnees_patient?.patient_normalized
  
  return {
    // Métadonnées
    session_id: rawData.session_id,
    user_id: rawData.user_id,
    last_update: rawData.last_update,
    available_outputs: rawData.available_outputs || [],
    
    // ============ AGENT COLLECTEUR ============
    patient: patient ? {
      // Identité
      id: patient.id,
      age: patient.age,
      sex: patient.sex,
      source_type: patient.source_type,
      
      // Admission
      admission: {
        type: patient.admission?.type,
        chief_complaint: patient.admission?.chief_complaint,
        date: patient.admission?.date,
        location: patient.admission?.location,
      },
      
      // Signes vitaux
      vitals: patient.vitals_current || {},
      
      // Examens biologiques
      labs: (patient.labs || []).map(lab => ({
        itemid: lab.itemid,
        charttime: lab.charttime,
        value: lab.value,
        valuenum: lab.valuenum,
        valueuom: lab.valueuom,
        flag: lab.flag,
        isAbnormal: lab.flag === 'abnormal'
      })),
      
      // Cultures microbiologiques
      cultures: (patient.cultures || []).map(culture => ({
        charttime: culture.charttime,
        spec_type: culture.spec_type,
        organism: culture.organism,
        status: culture.status,
        antibiotic: culture.antibiotic,
        interpretation: culture.interpretation,
        isPositive: culture.status === 'POSITIVE',
        isResistant: culture.interpretation === 'R',
        isSensitive: culture.interpretation === 'S',
        isIntermediate: culture.interpretation === 'I',
      })),
      
      // Diagnostics
      diagnoses: patient.diagnoses_icd || [],
      
      // Procédures
      procedures: patient.procedures_icd || [],
      
      // Médicaments
      medications: (patient.medications_current || []).map(med => ({
        drug: med.drug,
        dose: med.dose,
        route: med.route,
        startdate: med.startdate,
      })),
      
      // Historique médical
      medical_history: {
        known_conditions: patient.medical_history?.known_conditions || [],
        icu_stays: patient.medical_history?.icu_stays || 0,
      },
      
      // Informations de décès
      death_info: {
        expired: patient.death_info?.expired || false,
        dod: patient.death_info?.dod,
        hospital_expire: patient.death_info?.hospital_expire || false,
      }
    } : null,
    
    // ============ AGENT SYNTHÉTISEUR ============
    synthesis: synthese_clinique ? {
      // Alertes critiques
      critical_alerts: (synthese_clinique.critical_alerts || []).map(alert => ({
        type: alert.type,
        severity: alert.severity,
        finding: alert.finding,
        action_required: alert.action_required,
        isCritical: alert.severity === 'CRITICAL',
        isHigh: alert.severity === 'HIGH',
      })),
      
      // Incohérences
      data_inconsistencies: (synthese_clinique.data_inconsistencies || []).map(inc => ({
        field_1: inc.field_1,
        value_1: inc.value_1,
        field_2: inc.field_2,
        value_2: inc.value_2,
        explanation: inc.explanation,
      })),
      
      // Évaluation de fiabilité
      reliability: {
        completeness: synthese_clinique.reliability_assessment?.dossier_completeness || 0,
        confidence_level: synthese_clinique.reliability_assessment?.confidence_level,
        critical_missing: synthese_clinique.reliability_assessment?.critical_data_missing || [],
        quality_issues: synthese_clinique.reliability_assessment?.data_quality_issues || [],
      },
      
      // Scores cliniques
      clinical_scores: (synthese_clinique.clinical_scores || []).map(score => ({
        name: score.score_name,
        value: score.value,
        interpretation: score.interpretation,
        evidence: score.evidence || [],
      })),
      
      // Analyse de détérioration
      deterioration: {
        risk_level: synthese_clinique.deterioration_analysis?.risk_level,
        warning_signs: synthese_clinique.deterioration_analysis?.warning_signs || [],
        predicted_timeline: synthese_clinique.deterioration_analysis?.predicted_timeline,
        evidence: synthese_clinique.deterioration_analysis?.evidence || [],
        isCritical: synthese_clinique.deterioration_analysis?.risk_level === 'CRITICAL',
        isHigh: synthese_clinique.deterioration_analysis?.risk_level === 'HIGH',
      }
    } : null,
    
    // ============ AGENT EXPERT ============
    expert: validation_expert ? {
      // Diagnostics différentiels
      differential_diagnoses: (validation_expert.differential_diagnoses || []).map(diag => ({
        diagnosis: diag.diagnosis,
        probability: diag.probability,
        confidence: diag.confidence,
        supporting_evidence: (diag.supporting_evidence || []).map(ev => ({
          source: ev.source,
          statement: ev.statement,
        })),
        contradicting_evidence: (diag.contradicting_evidence || []).map(ev => ({
          source: ev.source,
          statement: ev.statement,
        })),
        isHighProbability: diag.probability === 'VERY_HIGH' || diag.probability === 'HIGH',
        isHighConfidence: diag.confidence === 'HIGH',
      })),
      
      // Validations des guidelines
      guideline_validations: (validation_expert.guideline_validations || []).map(val => ({
        alert_type: val.alert_type,
        guideline_source: val.guideline_source,
        recommendation: val.recommendation,
        compliance: val.compliance,
        evidence_strength: val.evidence_strength,
        references: val.references || [],
        isCompliant: val.compliance === 'COMPLIANT',
        isNonCompliant: val.compliance === 'NON_COMPLIANT',
        isStrongEvidence: val.evidence_strength === 'STRONG' || val.evidence_strength === 'HIGH',
      })),
      
      // Scores de risque
      risk_scores: (validation_expert.risk_scores || []).map(score => ({
        name: score.score_name,
        value: score.value,
        interpretation: score.interpretation,
        guideline_reference: score.guideline_reference,
      })),
      
      // Plan d'action détaillé
      action_plan: {
        immediate_actions: (validation_expert.action_plan?.immediate_actions || []).map(action => ({
          action: action.action,
          priority: action.priority || 'IMMEDIATE',
          rationale: action.rationale,
          time_window: action.time_window,
        })),
        urgent_actions: (validation_expert.action_plan?.urgent_actions || []).map(action => ({
          action: action.action,
          priority: action.priority || 'URGENT',
          rationale: action.rationale,
          time_window: action.time_window,
        })),
        diagnostic_workup: (validation_expert.action_plan?.diagnostic_workup || []).map(action => ({
          action: action.action,
          priority: action.priority,
          rationale: action.rationale,
          time_window: action.time_window,
        })),
        all_actions: [
          ...(validation_expert.action_plan?.immediate_actions || []),
          ...(validation_expert.action_plan?.urgent_actions || []),
          ...(validation_expert.action_plan?.diagnostic_workup || []),
        ]
      },
      
      // Synthèse des preuves
      evidence_summary: {
        key_findings: validation_expert.evidence_summary?.key_findings || [],
        references_used: validation_expert.evidence_summary?.references_used || [],
        methodology_note: validation_expert.evidence_summary?.methodology_note,
      }
    } : null,
    
    // Données brutes (pour debug)
    _raw: {
      donnees_patient,
      synthese_clinique,
      validation_expert,
    }
  }
}

// Ajouter cette fonction à lib/api.js

/**
 * Récupère la trace d'exécution de l'agent
 * Montre les tool calls, messages, et timeline
 */
export async function getExecutionTrace(userId, sessionId) {
  try {
    const response = await fetch(`${API_BASE_URL}/get_execution_trace`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        user_id: userId,
        session_id: sessionId,
      }),
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const data = await response.json()
    
    if (data.error) {
      throw new Error(data.error)
    }

    return {
      sessionId: data.session_id,
      userId: data.user_id,
      trace: data.execution_trace,
      statistics: data.statistics,
      state: data.state,
      lastUpdate: data.last_update,
    }
  } catch (error) {
    console.error('Erreur lors de la récupération de la trace d\'exécution:', error)
    throw error
  }
}