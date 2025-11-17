{
  "differential_diagnoses": [
    {
      "diagnosis": "Pneumonie sévère avec sepsis",
      "icd10_code": "J18.9",
      "probability": "HIGH",
      "confidence_score": 0.92,
      "supporting_evidence": [
        {"finding": "Fièvre 39.2°C", "strength": "STRONG"},
        {"finding": "Leucocytose à 18k", "strength": "STRONG"},
        {"finding": "Hypotension 92/54", "strength": "DEFINITIVE"}
      ],
      "contradicting_evidence": [],
      "additional_tests_needed": ["Hémocultures", "Gaz du sang", "RX thorax"],
      "urgency": "IMMEDIATE",
      "typical_presentation": "Fièvre, toux, hypotension, sepsis",
      "atypical_features": []
    },
    {
      "diagnosis": "Choc septique",
      "icd10_code": "R57.2",
      "probability": "HIGH",
      "confidence_score": 0.88,
      "supporting_evidence": [
        {"finding": "Lactate 4.1", "strength": "DEFINITIVE"},
        {"finding": "Hypotension persistante", "strength": "STRONG"}
      ],
      "contradicting_evidence": [],
      "additional_tests_needed": ["SAPS II", "Hémocultures", "Procalcitonine"],
      "urgency": "IMMEDIATE"
    }
  ],

  "validated_alerts": [
    {
      "type": "SEPSIS_CRITIQUE",
      "finding": "Lactate 4.1 mmol/L",
      "validation": {
        "alert_validated": true,
        "validation_strength": "STRONG",
        "guidelines_references": [
          {
            "guideline_name": "Surviving Sepsis Campaign 2021",
            "recommendation": "Administrer 30 ml/kg de cristalloïdes dans l'heure",
            "strength_of_evidence": "HIGH",
            "source_url": "https://.../ssc2021",
            "quote": "Initial fluid resuscitation of 30 mL/kg is recommended..."
          }
        ],
        "action_urgency_validated": "IMMEDIATE",
        "contraindications_check": {"contraindications_present": false}
      }
    },
    {
      "type": "INSUFF_RESP",
      "validation": {
        "alert_validated": true,
        "validation_strength": "MODERATE",
        "guidelines_references": [
          {
            "guideline_name": "ATS/IDSA Pneumonia Guidelines 2019",
            "recommendation": "Administration d'O2 pour maintenir SpO2 > 92%",
            "strength_of_evidence": "MODERATE"
          }
        ]
      }
    }
  ],

  "risk_scores": [
    {
      "diagnosis_related": "Sepsis",
      "score_name": "SAPS II",
      "score_value": 49,
      "interpretation": "Mortalité > 40%",
      "risk_category": "HIGH",
      "predicted_outcomes": {
        "mortality_30d": "40–50%",
        "complications": ["Choc", "IRA"],
        "icu_length_of_stay": "5–9 jours"
      }
    }
  ],

  "action_plan": {
    "immediate_actions": [
      {
        "action": "Administrer 30 ml/kg de cristalloïdes",
        "justification": "Hypotension + lactate élevé",
        "guideline_reference": "Surviving Sepsis 2021",
        "expected_outcome": "Amélioration perfusion"
      }
    ],
    "urgent_actions": [
      {
        "action": "Débuter antibiothérapie large spectre",
        "timeframe": "< 1h"
      }
    ],
    "diagnostic_workup": [
      {"test": "Hémocultures", "priority": "HIGH"},
      {"test": "RX thorax", "priority": "HIGH"}
    ],
    "monitoring_plan": [
      {"parameter": "PA, FC, lactate", "frequency": "q30min"}
    ],
    "disposition": {
      "recommended_location": "ICU",
      "justification": "Choc septique probable"
    }
  },

  "evidence_summary": {
    "total_references": 3,
    "guidelines_cited": [
      "Surviving Sepsis 2021",
      "ATS/IDSA Pneumonia 2019"
    ],
    "evidence_strength_summary": {
      "high_quality": 1,
      "moderate_quality": 2,
      "low_quality": 0
    }
  }
}
