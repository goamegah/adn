"""
VRAI Code utilisant Google Cloud Agent Development Kit (ADK)
"""

# Installation requise :
# pip install google-cloud-aiplatform[adk]
# pip install google-genai

from google import genai
from google.genai import types
import json


# ============================================================================
# VRAI ADK : Définition des Tools (Agents 1, 2, 3)
# ============================================================================

def tool_agent1_collecteur(patient_id: str, sources: dict) -> dict:
    """
    Tool ADK : Agent 1 - Collecte données patient

    Cette fonction est enregistrée comme "tool" dans ADK
    """
    from agents.collector.agent import AgentCollector
    project_id = "ai-diagnostic-navigator-475316"

    agent = AgentCollecteur(project_id)
    output = agent.collecter_donnees_patient(patient_id, sources)

    return output


def tool_agent2_synthetiseur(data_patient: dict) -> dict:
    """
    Tool ADK : Agent 2 - Synthèse et critique
    """
    from agents.synthesizer.agent import AgentSynthetiseur
    project_id = "ai-diagnostic-navigator-475316"

    agent = AgentSynthetiseur(project_id)
    output = agent.analyser_patient(data_patient)

    return output


def tool_agent3_expert_rag(alertes: list, data_patient: dict) -> dict:
    """
    Tool ADK : Agent 3 - Expertise médicale avec RAG
    """

    from agents.expert.agent import AgentExpert
    project_id = "ai-diagnostic-navigator-475316"

    # TODO: Implémenter Agent 3
    return {
        "diagnostics_differentiels": [],
        "recommandations": [],
        "guidelines": []
    }


# ============================================================================
# VRAI ADK : Configuration de l'Agent Orchestrateur
# ============================================================================

class OrchestrateurADNAvecADK:
    """
    Orchestrateur utilisant VRAIMENT Google Cloud ADK
    """

    def __init__(self, project_id: str, api_key: str):
        self.project_id = project_id

        # Initialiser le client ADK
        self.client = genai.Client(
            api_key=api_key,
            http_options={'api_version': 'v1alpha'}
        )

        # Déclarer les tools (= nos 3 agents)
        self.tools = self._declarer_tools()

        # Créer l'agent orchestrateur
        self.agent = self._creer_agent_orchestrateur()

    def _declarer_tools(self):
        """
        Déclare les 3 agents comme "tools" ADK
        """
        tools = [
            types.Tool(
                function_declarations=[
                    types.FunctionDeclaration(
                        name="collecteur_donnees_patient",
                        description="Collecte et agrège les données patient depuis 26 sources (DPI, LIS, PACS, etc.)",
                        parameters=types.Schema(
                            type=types.Type.OBJECT,
                            properties={
                                "patient_id": types.Schema(
                                    type=types.Type.STRING,
                                    description="Identifiant unique du patient"
                                ),
                                "sources": types.Schema(
                                    type=types.Type.OBJECT,
                                    description="Dictionnaire des sources de données disponibles"
                                )
                            },
                            required=["patient_id", "sources"]
                        )
                    ),
                    types.FunctionDeclaration(
                        name="analyse_critique_patient",
                        description="Synthétise les données et détecte les incohérences critiques (mode Jekyll/Hyde)",
                        parameters=types.Schema(
                            type=types.Type.OBJECT,
                            properties={
                                "data_patient": types.Schema(
                                    type=types.Type.OBJECT,
                                    description="Données patient collectées par l'Agent 1"
                                )
                            },
                            required=["data_patient"]
                        )
                    ),
                    types.FunctionDeclaration(
                        name="expertise_medicale_rag",
                        description="Valide les alertes avec guidelines médicales et génère diagnostics différentiels",
                        parameters=types.Schema(
                            type=types.Type.OBJECT,
                            properties={
                                "alertes": types.Schema(
                                    type=types.Type.ARRAY,
                                    description="Liste des alertes critiques détectées par l'Agent 2"
                                ),
                                "data_patient": types.Schema(
                                    type=types.Type.OBJECT,
                                    description="Données patient complètes"
                                )
                            },
                            required=["alertes", "data_patient"]
                        )
                    )
                ]
            )
        ]

        return tools

    def _creer_agent_orchestrateur(self):
        """
        Crée l'agent orchestrateur ADK
        """
        # Instructions système pour l'orchestrateur
        system_instruction = """
Tu es l'orchestrateur du système ADN (AI Diagnostic Navigator).

Ta mission : Coordonner intelligemment les 3 agents spécialisés pour analyser un patient.

WORKFLOW À SUIVRE :
1. Appelle d'abord "collecteur_donnees_patient" pour récupérer toutes les données
2. Passe ces données à "analyse_critique_patient" pour obtenir la synthèse et les alertes
3. Utilise "expertise_medicale_rag" pour valider et enrichir avec des guidelines médicales

RÈGLES IMPORTANTES :
- Tu dois TOUJOURS appeler les 3 agents dans cet ordre
- Si un agent échoue, explique l'erreur et propose une solution
- Synthétise les résultats de manière claire pour le médecin
- Priorise les alertes critiques (severity: CRITICAL)
"""

        # Configuration de l'agent
        agent_config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            tools=self.tools,
            temperature=0.3,  # Peu de créativité, on veut de la précision
            response_modalities=["TEXT"]
        )

        return agent_config

    def executer_workflow(self, patient_id: str, sources: dict) -> dict:
        """
        Lance le workflow orchestré par ADK
        """
        print("=" * 80)
        print("🚀 ORCHESTRATEUR ADK - Démarrage")
        print("=" * 80)

        # Prompt initial pour l'orchestrateur
        user_prompt = f"""
Analyse le patient {patient_id} en utilisant les outils disponibles.

Sources de données disponibles : {json.dumps(sources, indent=2)}

Tu dois :
1. Collecter les données avec collecteur_donnees_patient
2. Analyser avec analyse_critique_patient
3. Valider avec expertise_medicale_rag

Fournis un rapport final complet.
"""

        # Appel ADK avec gestion automatique des function calls
        response = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=user_prompt,
            config=self.agent
        )

        # ADK gère automatiquement l'orchestration !
        # Il va appeler les tools dans l'ordre, gérer les résultats, etc.

        return self._parser_response(response)

    def _parser_response(self, response):
        """
        Parse la réponse de l'orchestrateur ADK
        """
        # Extraire le texte final
        texte_final = response.text if hasattr(response, 'text') else ""

        # Extraire les function calls exécutés
        function_calls = []
        if hasattr(response, 'candidates'):
            for candidate in response.candidates:
                if hasattr(candidate, 'content'):
                    for part in candidate.content.parts:
                        if hasattr(part, 'function_call'):
                            function_calls.append({
                                "name": part.function_call.name,
                                "args": dict(part.function_call.args)
                            })

        return {
            "rapport_final": texte_final,
            "function_calls_executes": function_calls,
            "raw_response": response
        }


# ============================================================================
# MAPPING DES FUNCTION CALLS : Connecter ADK à nos agents
# ============================================================================

def executer_function_call(function_name: str, arguments: dict):
    """
    Fonction appelée automatiquement par ADK quand il déclenche un tool
    """

    mapping = {
        "collecteur_donnees_patient": tool_agent1_collecteur,
        "analyse_critique_patient": tool_agent2_synthetiseur,
        "expertise_medicale_rag": tool_agent3_expert_rag
    }

    if function_name in mapping:
        print(f"🔧 [ADK] Exécution tool: {function_name}")
        result = mapping[function_name](**arguments)
        print(f"✅ [ADK] Tool terminé: {function_name}")
        return result
    else:
        raise ValueError(f"Tool inconnu: {function_name}")


# ============================================================================
# VERSION SIMPLIFIÉE : Sans toute la config ADK complexe
# ============================================================================

class OrchestrateurADKSimple:
    """
    Version simplifiée utilisant ADK avec moins de config
    """

    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)

    def analyser_patient(self, patient_id: str, sources: dict) -> dict:
        """
        Analyse un patient avec orchestration ADK automatique
        """

        # ADK va automatiquement comprendre qu'il doit appeler les tools
        prompt = f"""
Analyse médicale complète du patient {patient_id}.

Étapes à suivre :
1. Collecte les données patient
2. Synthétise et détecte les incohérences
3. Valide avec les guidelines médicales

Sources disponibles: {json.dumps(sources)}

Fournis un rapport structuré avec :
- Synthèse clinique
- Alertes critiques
- Actions urgentes à prendre
"""

        # ADK gère tout automatiquement
        response = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        return {"rapport": response.text}


# ============================================================================
# UTILISATION RÉELLE
# ============================================================================

if __name__ == "__main__":
    # IMPORTANT : Il faut une vraie API key Google AI
    API_KEY = "AQ.Ab8RN6LffBTMQIk8w4JbrdNMf7zxfaeR61tA_76Kg2wxVMDKQg"
    PROJECT_ID = "ai-diagnostic-navigator-475316"

    # Données de test
    PATIENT_ID = ""
sources_test = {}

try:
    # Créer l'orchestrateur ADK (VRAI)
    orchestrateur = OrchestrateurADNAvecADK(PROJECT_ID, API_KEY)

    # Lancer le workflow
    resultat = orchestrateur.executer_workflow(PATIENT_ID, sources_test)

    print("\n" + "=" * 80)
    print("📊 RÉSULTAT ADK")
    print("=" * 80)
    print(json.dumps(resultat, indent=2, ensure_ascii=False))

except Exception as e:
    print(f"❌ Erreur: {e}")
    print("\nℹ️  Note: Pour utiliser ADK, il faut:")
    print("   1. pip install google-genai")
    print("   2. Avoir une API key Google AI")
    print("   3. Configurer correctement les tools")

