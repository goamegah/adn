class CollectorAgent:
    """Version temporaire de l'agent de collecte, pour tester l'infrastructure de test."""

    def process(self, text: str):
        # Retourne une structure minimale conforme à ton output attendu
        return {
            "incident_description": {"main_reason": "douleur thoracique après malaise"},
            "patient_identification": {"age": 58},
            "caller_info": {"relationship_to_patient": "épouse"},
            "location": {"city": "Lyon"}
        }
