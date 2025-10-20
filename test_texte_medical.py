#!/usr/bin/env python3
"""
Test de l'orchestrateur avec un texte médical
"""

import sys
import os

# Ajouter le répertoire racine au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.collector.agent import AgentCollecteur
from agents.synthesizer.agent import AgentSynthetiseur
from agents.expert.agent import AgentExpert


# Exemple de texte médical
TEXTE_MEDICAL = """
Patiente de 68 ans, diabétique type 2 sous metformine, hypertendue sous ramipril.

Motif de consultation : Douleur thoracique constrictive depuis 3 heures, irradiant dans le bras gauche.
Antécédents : Infarctus il y a 5 ans, stent sur IVA. Tabagisme sevré depuis 2 ans.

Examen clinique :
- TA : 145/92 mmHg
- FC : 98 bpm, régulier
- SpO2 : 96% air ambiant
- Auscultation cardiaque : B1 B2 normaux, pas de souffle
- Auscultation pulmonaire : MV présents, pas de râles

ECG : Sus-décalage du segment ST en territoire antérieur (V2-V4)

Biologie :
- Troponine Ic : 3.2 ng/mL (N < 0.04)
- CK-MB : 45 U/L (N < 25)
- D-dimères : 180 ng/mL (N < 500)

Impression clinique : Syndrome coronarien aigu avec sus-décalage du ST (STEMI)
"""


def test_texte_medical():
    """Test du pipeline complet avec texte médical"""
    
    PROJECT_ID = "ai-diagnostic-navigator-475316"
    
    print("="*100)
    print("🧪 TEST : Pipeline ADN avec TEXTE MÉDICAL")
    print("="*100)
    
    # Agent 1 : Collecteur
    print("\n🔵 Agent 1 : Collecteur")
    agent1 = AgentCollecteur()
    data = agent1.collecter_donnees_patient(texte_medical=TEXTE_MEDICAL)
    print(f"✅ Données collectées (source: {data['patient_normalized']['source_type']})")
    
    # Agent 2 : Synthétiseur
    print("\n🟢 Agent 2 : Synthétiseur/Critique")
    agent2 = AgentSynthetiseur(project_id=PROJECT_ID)
    synthese = agent2.analyser_patient(data)
    print(f"✅ Synthèse terminée")
    print(f"   Sévérité: {synthese['synthesis'].get('severity', 'N/A')}")
    print(f"   Alertes: {len(synthese['critical_alerts'])}")
    
    # Agent 3 : Expert
    print("\n🟣 Agent 3 : Expert/RAG")
    agent3 = AgentExpert(project_id=PROJECT_ID)
    expert = agent3.analyser_alertes(synthese)
    print(f"✅ Expertise terminée")
    print(f"   Diagnostics différentiels: {len(expert['differential_diagnoses'])}")
    
    # Résumé
    print("\n" + "="*100)
    print("📋 RÉSUMÉ")
    print("="*100)
    
    print("\n🩺 DIAGNOSTICS DIFFÉRENTIELS:")
    for i, dx in enumerate(expert['differential_diagnoses'][:3], 1):
        print(f"   {i}. {dx.get('diagnosis', 'N/A')} - {dx.get('probability', 'N/A')}")
    
    print("\n🚨 ALERTES CRITIQUES:")
    for i, alerte in enumerate(synthese['critical_alerts'][:3], 1):
        print(f"   {i}. {alerte.get('type', 'N/A')}")
        print(f"      → {alerte.get('finding', 'N/A')}")
    
    print("\n💊 ACTIONS IMMÉDIATES:")
    actions = expert['action_plan'].get('immediate_actions', [])
    for i, action in enumerate(actions[:3], 1):
        print(f"   {i}. {action.get('action', 'N/A')}")
    
    print("\n" + "="*100)
    print("✅ TEST TERMINÉ")
    print("="*100)


if __name__ == "__main__":
    test_texte_medical()