"""
Agent de classification des transcripts ARM
"""
from typing import Dict, Any, List
import vertexai
from vertexai.generative_models import GenerativeModel
import os
from agents.base_agent import BaseAgent


class ARMClassifierAgent(BaseAgent):
    
    PATHOLOGIES = [
        "ARRÊT CARDIAQUE",
        "ARRÊT CARDIAQUE ADULTE",
        "HÉMORAGIE INTERNE",
        "HÉMORRAGIE EXTÉRIORISÉE",
        "INTOXICATION ÉTHYLIQUE",
        "INTOXICATION MÉDICAMENTEUSE",
        "MALAISE",
        "PROBLÈME RESPIRATOIRE",
    ]
    
    def __init__(self, name: str = "ARM Classifier", config: Dict[str, Any] = None):
        super().__init__(name, config)
        vertexai.init(project=os.getenv("GCP_PROJECT_ID"), location=os.getenv("GCP_REGION", "europe-west1"))
        self.model = GenerativeModel("gemini-2.0-flash")
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        transcript = input_data.get("transcript", "")
        
        pathologies_list = "\n".join(self.PATHOLOGIES)
        
        prompt = f"""Classifie ce transcript parmi ces pathologies (tu peux en choisir plusieurs si pertinent):

{pathologies_list}

Transcript: {transcript}

Réponds avec les noms EXACTS des pathologies, une par ligne."""
        
        response = self.model.generate_content(prompt)
        
        # Parser les lignes de réponse
        classifications = []
        for line in response.text.strip().split('\n'):
            line = line.strip()
            if line in self.PATHOLOGIES:
                classifications.append(line)
        
        # Fallback si aucune pathologie valide
        if not classifications:
            classifications = ["MALAISE"]
        
        return {
            "classifications": classifications,
            "confidence": 0.5
        }


if __name__ == "__main__":
    import asyncio
    from dotenv import load_dotenv
    
    load_dotenv()
    
    async def test_simple():
        agent = ARMClassifierAgent()
        transcript = "Mon mari ne respire plus, il est inconscient et saigne beaucoup"
        result = await agent.process({"transcript": transcript})
        print(result)
    
    asyncio.run(test_simple())