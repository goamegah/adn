# 🚨 Système Multi-Agents ARM - Régulation Médicale d'Urgence

Système d'assistance intelligente pour les Assistants de Régulation Médicale (ARM) utilisant Google Cloud ADK avec architecture multi-agents.

## 📋 Vue d'ensemble

Ce système déploie trois agents spécialisés travaillant en collaboration pour assister les ARM dans la gestion des appels d'urgence médicale :

- **ARM Agent** : Orchestrateur principal du système de régulation
- **Clinical Agent** : Agent de diagnostic et analyse médicale
- **Speech-to-Text Agent** : Agent de transcription en temps réel

---

## 🏗️ Architecture des Agents

### 1. ARM Agent (`arm_agent/`)

**Rôle** : Orchestrateur principal du système de régulation médicale d'urgence.

#### Agents internes

##### 🔍 `call_classifier_agent`
**Description** : Classification automatique des appels d'urgence

**Mission** :
- Analyse les transcriptions d'appels pour identifier le type d'urgence
- Catégorise parmi 8 types d'urgence prédéfinis

**Catégories supportées** :
- `ARRÊT CARDIAQUE` / `ARRÊT CARDIAQUE ADULTE`
- `HÉMORAGIE INTERNE`
- `HÉMORRAGIE EXTÉRIORISÉE`
- `INTOXICATION ÉTHYLIQUE`
- `INTOXICATION MÉDICAMENTEUSE`
- `MALAISE`
- `PROBLÈME RESPIRATOIRE`

**Output** : Nom exact de la catégorie ou `NON CLASSIFIABLE`

##### 🧭 `call_guiding_agent`
**Description** : Création de guides d'appel structurés (arbres décisionnels)

**Mission** :
- Génère des protocoles de triage adaptés au type d'urgence
- Fournit des questions structurées et des instructions de premiers secours

**Output** : Arbre décisionnel avec :
- Questions de triage initiales
- Informations essentielles à collecter
- Instructions pour l'appelant
- Décisions de transmission (SAMU/POMPIERS/MÉDECIN)

##### 🚨 `call_decision_agent`
**Description** : Décision de prise en charge en situation d'urgence

**Mission** :
- Détermine le service approprié à déclencher
- Analyse la gravité et l'urgence de la situation

**Options de décision** :
- 🚑 `SMUR` - Urgence vitale immédiate
- 🚒 `POMPIERS` - Secours technique, désincarcération
- 👩‍⚕️ `MEDECIN_REGULATEUR` - Avis médical urgent
- 🏥 `AUTRE` - Consultation différée ou surveillance

**Output format** :
```json
{
  "decision": "SMUR",
  "justification": "Arrêt cardiaque confirmé, RCP en cours"
}
```

##### 🎯 `root_agent` (ARM_assistant_agent)
**Description** : Agent racine orchestrant l'ensemble du workflow

**Workflow** :
1. Analyse la transcription complète de l'appel
2. Appelle `call_classifier_agent` pour identifier le type
3. Appelle `call_guiding_agent` pour générer le guide
4. Appelle `call_decision_agent` pour déterminer le service
5. Maintient un état synthétique de la session

**Tools disponibles** :
- `call_classifier_agent_tool`
- `call_guiding_agent_tool`
- `call_decision_agent_tool`

**Output format** :
```json
{
  "type_appel": "ARRÊT CARDIAQUE",
  "decision": "SMUR",
  "justification": "Patient inconscient, absence de pouls détectée",
  "actions_recommandées": ["Débuter RCP immédiatement", "Envoyer SMUR en urgence absolue"]
}
```

#### Modèle utilisé
```python
MODEL = "gemini-2.0-flash-exp"
```

---

### 2. Clinical Agent (`clinical_agent/`)

**Rôle** : Agent de diagnostic et analyse médicale approfondie.

**Fonctionnalités** :
- Analyse des symptômes et signes cliniques
- Aide au diagnostic différentiel
- Suggestions de protocoles médicaux
- Évaluation de la gravité (scores qSOFA, SOFA)

**Note** : Détails complets à venir selon votre implémentation spécifique.

---

### 3. Speech-to-Text Agent (`speech_to_text_agent/`)

**Rôle** : Transcription en temps réel des appels d'urgence.

**Fonctionnalités** :
- Streaming audio bidirectionnel
- Transcription continue via Google Speech-to-Text
- Détection de symptômes en temps réel
- Déduplication d'alertes

**Services** :
- Transcription streaming
- Détection de mots-clés critiques
- Génération d'alertes pour l'ARM

---

## 🧪 Tester avec ADK Web

### Prérequis

1. **Installation du Google ADK** :
```bash
pip install google-adk
```

2. **Authentification GCP** :
```bash
gcloud auth application-default login
export GOOGLE_CLOUD_PROJECT="your-project-id"
```

### Démarrage de l'interface web

#### Option 1 : Tester un agent spécifique

**ARM Agent** :
```bash
cd arm_agent
adk web
```

**Clinical Agent** :
```bash
cd clinical_agent
adk web
```

**Speech-to-Text Agent** :
```bash
cd speech_to_text_agent
adk web
```

#### Option 2 : Démarrer tous les agents

Depuis la racine du projet :
```bash
# Terminal 1
cd arm_agent && adk web --port 8001

# Terminal 2
cd clinical_agent && adk web --port 8002

# Terminal 3
cd speech_to_text_agent && adk web --port 8003
```

### Interface Web ADK

Une fois lancé, l'interface sera accessible à :
```
http://localhost:8000
```

Vous verrez :
- 📊 Liste des agents disponibles
- 💬 Interface de chat pour interagir
- 🔧 Panneau de configuration des tools
- 📝 Historique des appels d'outils

---

## 🎯 Scénarios de Test

### Test 1 : Classification d'appel simple

**Input** :
```
Transcription : "Mon mari est tombé, il ne respire plus et il est inconscient. Je ne sens pas son pouls."
```

**Workflow attendu** :
1. `root_agent` reçoit la transcription
2. Appelle `call_classifier_agent` → Output: `ARRÊT CARDIAQUE`
3. Appelle `call_guiding_agent` → Génère protocole RCP
4. Appelle `call_decision_agent` → Output: `SMUR`

**Commande de test** :
```
Utilisateur : "Analyse cet appel : Mon mari est tombé, il ne respire plus et il est inconscient. Je ne sens pas son pouls."
```

---

### Test 2 : Appel avec hémorragie

**Input** :
```
"Ma femme s'est coupée avec un couteau, elle saigne beaucoup de l'avant-bras, le sang coule par terre."
```

**Classification attendue** : `HÉMORRAGIE EXTÉRIORISÉE`

**Décision attendue** : `POMPIERS` ou `SMUR` selon la gravité

---

### Test 3 : Malaise non critique

**Input** :
```
"Mon père a eu un vertige, il est tombé mais il est conscient maintenant. Il a 75 ans et il a mal à la tête."
```

**Classification attendue** : `MALAISE`

**Décision attendue** : `MEDECIN_REGULATEUR` ou `AUTRE`

---

### Test 4 : Intoxication médicamenteuse

**Input** :
```
"J'ai trouvé ma fille avec une boîte de médicaments vide. Elle a 16 ans, elle est consciente mais somnolente."
```

**Classification attendue** : `INTOXICATION MÉDICAMENTEUSE`

**Décision attendue** : `SMUR`

---

## 🔍 Debugging et Logs

### Activer les logs détaillés

```bash
export ADK_LOG_LEVEL=DEBUG
adk web
```

### Visualiser les appels d'outils

Dans l'interface web ADK, le panneau "Tool Calls" affiche :
- Quel agent a été appelé
- Avec quels paramètres
- La réponse retournée
- Le temps d'exécution

### Tester les tools individuellement

Vous pouvez tester chaque sous-agent directement :

```python
# Dans la console Python
from arm_agent.agent import call_classifier_agent

response = call_classifier_agent.generate(
    "Mon mari ne respire plus, il est inconscient."
)
print(response.text)
```

---

## 📦 Structure des fichiers

```
agents/
├── arm_agent/
│   ├── agent.py              # Définition des agents ARM
│   ├── __init__.py
│   └── requirements.txt
├── clinical_agent/
│   ├── agent.py              # Agent de diagnostic médical
│   ├── __init__.py
│   └── requirements.txt
└── speech_to_text_agent/
    ├── agent.py              # Agent de transcription
    ├── __init__.py
    └── requirements.txt
```

---

## 🚀 Déploiement

### Cloud Run

Chaque agent peut être déployé individuellement sur Cloud Run :

```bash
# Exemple pour ARM Agent
cd arm_agent
gcloud run deploy arm-agent \
  --source . \
  --region europe-west1 \
  --allow-unauthenticated
```

### Communication inter-agents (A2A)

Les agents communiquent via le protocole A2A en utilisant les `.well-known/agent.json` endpoints.

---

## 📝 Configuration

### Variables d'environnement requises

```bash
export GOOGLE_CLOUD_PROJECT="your-project-id"
export GOOGLE_APPLICATION_CREDENTIALS="path/to/service-account.json"
export ADK_MODEL="gemini-2.0-flash-exp"
```

### Personnalisation des catégories

Modifiez la liste `CALL_TYPES` dans `arm_agent/agent.py` :

```python
CALL_TYPES = [
    "VOTRE_NOUVELLE_CATÉGORIE",
    # ...
]
```

---

## 🔐 Sécurité

⚠️ **Important** :
- Ne jamais exposer d'informations patient réelles en test
- Utiliser des données anonymisées
- Respecter les réglementations RGPD et e-santé
- Authentifier tous les endpoints de production

---

## 🤝 Contribution

Pour ajouter un nouveau type d'urgence :

1. Ajouter la catégorie dans `CALL_TYPES`
2. Mettre à jour les critères dans `call_classifier_agent.instruction`
3. Ajouter les protocoles correspondants dans `call_guiding_agent`
4. Tester avec des scénarios réalistes

---

## 📚 Ressources

- [Google ADK Documentation](https://cloud.google.com/agent-development-kit/docs)
- [A2A Protocol Specification](https://google.aip.dev/client-libraries/agent-to-agent)
- [Vertex AI Gemini Models](https://cloud.google.com/vertex-ai/docs/generative-ai/model-reference/gemini)

---

## 🆘 Support

En cas de problème :
1. Vérifier les logs avec `ADK_LOG_LEVEL=DEBUG`
2. Tester les agents individuellement
3. Valider l'authentification GCP
4. Vérifier les quotas Vertex AI

---

**Auteur** : Système ARM - Régulation Médicale  
**Version** : 1.0  
**Modèle** : Gemini 2.0 Flash Experimental