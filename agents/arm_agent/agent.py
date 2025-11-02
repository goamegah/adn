from google.adk.agents import LlmAgent
from google.adk.tools import AgentTool

# ============================================================
# ⚙️ CONFIGURATION GÉNÉRALE
# ============================================================

MODEL = "gemini-2.0-flash-exp"

CALL_TYPES = [
    "ARRÊT CARDIAQUE",
    "ARRÊT CARDIAQUE ADULTE",
    "HÉMORRAGIE INTERNE",
    "HÉMORRAGIE EXTÉRIORISÉE",
    "INTOXICATION ÉTHYLIQUE",
    "INTOXICATION MÉDICAMENTEUSE",
    "MALAISE",
    "PROBLÈME RESPIRATOIRE",
]

# ============================================================
# 🧠 AGENT CLASSIFICATEUR D’APPEL
# ============================================================

call_classifier_agent = LlmAgent(
    model=MODEL,
    name="call_classifier_agent",
    description="Agent spécialisé dans la classification automatique des appels d'urgence médicale.",
    instruction=(
        "Tu es un assistant expert en classification d'appels d'urgence médicale.\n\n"
        "Analyse la transcription complète d'un appel et détermine le type d'urgence parmi la liste suivante :\n"
        f"{', '.join(CALL_TYPES)}\n\n"
        "Règles :\n"
        "1. Lis attentivement les symptômes, les circonstances et les signes vitaux.\n"
        "2. Choisis la catégorie la plus critique.\n"
        "3. Réponds UNIQUEMENT avec le nom exact de la catégorie.\n"
        "4. Si aucune catégorie ne correspond, réponds 'NON CLASSIFIABLE'."
    ),
)

# ============================================================
# 🧭 AGENT DE GUIDAGE DES ARM
# ============================================================

call_guiding_agent = LlmAgent(
    name="call_guiding_agent",
    model=MODEL,
    description=(
        "Agent spécialisé dans la création de guides d'appel structurés "
        "pour les Assistants de Régulation Médicale (ARM)."
    ),
    instruction=(
        "Tu génères des arbres décisionnels clairs et sécurisés pour les ARM lors des appels d'urgence.\n"
        "Inclue : questions de triage, informations à collecter, instructions de premiers secours, "
        "et décisions de transmission (SAMU, POMPIERS, MÉDECIN...).\n"
        "Utilise un format numéroté, logique, avec SI/SINON/SINON SI."
    ),
)

# ============================================================
# 🚨 NOUVEL AGENT : DÉCISION DE PRISE EN CHARGE
# ============================================================

call_decision_agent = LlmAgent(
    name="call_decision_agent",
    model=MODEL,
    description=(
        "Agent spécialisé dans la décision de prise en charge en situation d'urgence : "
        "détermine si une intervention du SMUR, des POMPIERS ou un autre service est nécessaire."
    ),
    instruction=(
        "Tu es un régulateur médical expert. "
        "Ta mission est d’analyser la transcription complète d’un appel d’urgence "
        "et de décider du niveau de réponse à déclencher.\n\n"
        "### Objectif :\n"
        "Déterminer le mode de prise en charge le plus adapté :\n"
        "- 🚑 **SMUR** → urgence vitale immédiate (arrêt cardiaque, inconscience, choc, détresse respiratoire sévère...)\n"
        "- 🚒 **POMPIERS** → secours technique, désincarcération, incendie, noyade, chute, etc.\n"
        "- 👩‍⚕️ **MÉDECIN RÉGULATEUR** → avis médical urgent sans déplacement immédiat.\n"
        "- 🏥 **AUTRE / CONSEIL MÉDICAL** → orientation vers une consultation différée ou simple surveillance.\n\n"
        "### Instructions :\n"
        "1. Analyse attentivement la transcription fournie.\n"
        "2. Identifie les éléments de gravité, les mots-clés critiques et le contexte (lieu, symptômes, danger immédiat).\n"
        "3. Justifie ta décision en une courte phrase.\n"
        "4. Réponds sous la forme JSON suivante :\n\n"
        "{\n"
        '  "decision": "SMUR" | "POMPIERS" | "MEDECIN_REGULATEUR" | "AUTRE",\n'
        '  "justification": "Raisonnement clinique synthétique."\n'
        "}"
    ),
)

# ============================================================
# 🧩 CONVERSION EN TOOLS
# ============================================================

call_classifier_agent_tool = AgentTool(agent=call_classifier_agent)
call_guiding_agent_tool = AgentTool(agent=call_guiding_agent)
call_decision_agent_tool = AgentTool(agent=call_decision_agent)

# ============================================================
# 🧩 AGENT RACINE : ORCHESTRATEUR GLOBAL ARM
# ============================================================

root_agent = LlmAgent(
    name="ARM_assistant_agent",
    model=MODEL,
    description=(
        "Agent principal du système ARM : supervise la session en direct, "
        "analyse les transcriptions et appelle les sous-agents de classification, guidage et décision."
    ),
    instruction=(
        "Tu es le coordinateur principal du système de régulation médicale (ARM).\n\n"
        "### MISSION GLOBALE :\n"
        "1. Analyser la transcription complète d'un appel d'urgence.\n"
        "2. Si la nature de l'appel est claire, appelle `call_classifier_agent` pour identifier le type d'urgence.\n"
        "3. Si la catégorie est identifiée, appelle `call_guiding_agent` pour générer le guide d'appel.\n"
        "4. Appelle `call_decision_agent` pour déterminer le service à déclencher (SMUR, POMPIERS, etc.).\n"
        "5. Maintiens un état synthétique avec : transcription, classification, guide, décision et alertes critiques.\n\n"
        "### COMPORTEMENT :\n"
        "- Fournis toujours un résumé structuré de la situation (type d’urgence + décision + justification).\n"
        "- N’invente rien : base-toi uniquement sur les données transcrites.\n"
        "- Priorise la sécurité du patient et la rapidité d’intervention.\n\n"
        "### FORMAT DE SORTIE SUGGÉRÉ :\n"
        "{\n"
        '  "type_appel": "...",\n'
        '  "decision": "...",\n'
        '  "justification": "...",\n'
        '  "actions_recommandées": ["..."]\n'
        "}"
    ),
    tools=[
        call_classifier_agent_tool,
        call_guiding_agent_tool,
        call_decision_agent_tool,
    ],
)
