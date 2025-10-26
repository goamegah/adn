"""
Orchestrateur ADN - Version Debug RAW avec imports fixes
"""

import json
import sys
import os
from typing import Dict, Any

# FIX: Ajouter le répertoire racine au Python path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from agents.collector.agent import AgentCollecteur
from agents.synthesizer.agent import AgentSynthetiseur
from agents.expert.agent import AgentExpert


class OrchestrateurADN:
    """Orchestrateur simple qui enchaîne les 3 agents"""
    
    def __init__(self, project_id: str, data_dir: str = "/home/bao/adn/data/MIMIC 3 DATASET"):
        self.project_id = project_id
        self.data_dir = data_dir

        self.agent1 = AgentCollecteur(data_dir=data_dir)
        self.agent2 = AgentSynthetiseur()
        self.agent3 = AgentExpert(project_id=project_id)
    
    def analyser_patient(self, subject_id: int) -> Dict[str, Any]:        
        data_collectee = self.agent1.collecter_donnees_patient(subject_id)        
        resultat_synthese = self.agent2.analyser_patient(data_collectee)
        resultat_expert = self.agent3.analyser_alertes(resultat_synthese)
        return {
            "patient_id": subject_id,
            "agent1_collecteur": data_collectee,
            "agent2_synthetiseur": resultat_synthese,
            "agent3_expert": resultat_expert,
            "status": "success"
        }
        