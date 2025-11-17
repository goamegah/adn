{
  "synthesis": {
    "summary": "Homme de 65 ans avec dyspnée aiguë, fièvre, hypotension",
    "key_problems": ["Suspected pneumonia", "Hypotension", "Lactate élevé"],
    "severity": "HIGH",
    "clinical_trajectory": "WORSENING"
  },
  "critical_alerts": [
    {
      "type": "SEPSIS_CRITIQUE",
      "severity": "CRITICAL",
      "finding": "Lactate 4.1 mmol/L",
      "clinical_impact": "Risque de choc septique",
      "action_required": "Fluid challenge immédiat"
    },
    {
      "type": "INSUFF_RESP",
      "severity": "HIGH",
      "finding": "SpO2 88% sous 2L",
      "clinical_impact": "Défaillance respiratoire",
      "action_required": "Augmenter O2 ou passer en VNI"
    }
  ],
  "source_data": {
    "patient_normalized": {
      "age": 65,
      "sex": "homme",
      "medical_history": {
        "known_conditions": ["HTA", "Tabagisme chronique"]
      },
      "vitals_current": {
        "temperature": 39.2,
        "heart_rate": 122,
        "blood_pressure": "92/54",
        "spo2": 88
      },
      "labs": [
        {"name": "WBC", "value": 18000, "flag": "HIGH"},
        {"name": "Lactate", "value": 4.1, "flag": "HIGH"}
      ],
      "cultures": []
    }
  },
  "clinical_scores": [
    {"score_name": "qSOFA", "value": 3, "interpretation": "Risque très élevé"}
  ]
}
