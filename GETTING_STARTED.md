# Guide de Démarrage - ADN Full Stack

## Prérequis

- **Python 3.11+** avec environnement virtuel
- **Node.js 18+** et npm
- **Navigateur moderne** (Chrome, Firefox, Edge, Safari)

## Installation

### 1. Backend FastAPI

```bash
# Aller dans le répertoire du projet
cd /home/goamegah/Documents/develop/repo/adn

# Activer l'environnement virtuel (s'il existe déjà)
source .venv/bin/activate

# Installer les dépendances (si pas déjà fait)
cd backend
pip install -r requirements.txt
```

### 2. Frontend Next.js

```bash
# Aller dans le dossier frontend
cd /home/goamegah/Documents/develop/repo/adn/next_frontend

# Installer les dépendances (si pas déjà fait)
npm install
```

## ▶️ Lancement de l'Application

### Option 1 : Lancement Manuel (2 terminaux)

#### Terminal 1 - Backend
```bash
cd /home/goamegah/Documents/develop/repo/adn/backend/orchestrator
source ../../.venv/bin/activate # Activer l'env virtuel
uvicorn main:app --reload --port 8000

# Ou avec le chemin complet Python :
/home/goamegah/Documents/develop/repo/adn/.venv/bin/python -m uvicorn main:app --reload --port 8000
```

** Backend prêt** : http://127.0.0.1:8000

#### Terminal 2 - Frontend
```bash
cd /home/goamegah/Documents/develop/repo/adn/next_frontend
npm run dev
```

** Frontend prêt** : http://localhost:3000

### Option 2 : Script de Lancement (à venir)

Créez un fichier `start.sh` à la racine :

```bash
#!/bin/bash

# Lancer le backend en arrière-plan
cd backend/orchestrator
../../.venv/bin/python -m uvicorn main:app --reload --port 8000 &
BACKEND_PID=$!

# Lancer le frontend
cd ../../next_frontend
npm run dev &
FRONTEND_PID=$!

echo " Backend démarré (PID: $BACKEND_PID) sur http://127.0.0.1:8000"
echo " Frontend démarré (PID: $FRONTEND_PID) sur http://localhost:3000"

# Attendre et gérer l'arrêt propre
trap "kill $BACKEND_PID $FRONTEND_PID" EXIT
wait
```

Puis :
```bash
chmod +x start.sh
./start.sh
```

## Tester la Connexion

### 1. Vérifier le Backend

```bash
# Test simple
curl http://127.0.0.1:8000/health

# Devrait retourner :
# {"status":"healthy","service":"adn-orchestrator"}

# Test complet
curl -X POST http://127.0.0.1:8000/api/analyze \
 -H "Content-Type: application/json" \
 -d '{"patient_id":"PAT-TEST-001","query":"Analyse patient test"}'
```

### 2. Vérifier le Frontend

Ouvrez votre navigateur sur : **http://localhost:3000**

Vous devriez voir :
- Header avec logo ADN
- Champs de saisie (Patient ID + Prompt)
- Bouton "Analyser avec ADN"
- Bouton flottant de chat

## Utilisation de l'Application

### Étape 1 : Saisir les informations

1. **ID Patient** : `PAT-2024-1847` (ou un autre ID)
2. **Prompt clinique** : `Analyse patient avec dyspnée aiguë`

### Étape 2 : Lancer l'analyse

Cliquez sur **"Analyser avec ADN (4 agents)"**

### Étape 3 : Consulter les résultats

L'interface affiche 4 panels :

#### Panel 1 - Synthèse Patient (Agent Synthétiseur)
- Informations démographiques
- Antécédents médicaux
- Médicaments actuels
- Signes vitaux

#### Panel 2 - Diagnostics Différentiels (Agent Expert)
- Liste des hypothèses diagnostiques
- Probabilités (Élevée/Moyenne/Faible)
- Preuves à l'appui
- Scores de confiance
- Actions suggérées

#### ️ Panel 3 - Alertes Critiques (Agent Critique)
- Alertes de sévérité élevée (rouge)
- Warnings (jaune)
- Niveau de confiance

#### Panel 4 - Recommandations Immédiates
- Recommandations priorisées (1, 2, 3...)
- Catégories (Urgence, Monitoring, Biologie)
- Délais attendus

### Étape 4 : Utiliser le Chat

1. Cliquez sur le bouton flottant 
2. Posez des questions à l'assistant
3. Recevez des analyses en temps réel

## Responsive Design

L'interface s'adapte automatiquement :

- ** Mobile** (< 640px) : 
 - Layout vertical (1 colonne)
 - Chat en plein écran
 - Menus simplifiés

- ** Desktop** (> 1024px) :
 - Layout 2 colonnes
 - Chat en modal centré
 - Toutes les informations visibles

## Configuration

### Proxy API (Next.js)

Le fichier `next_frontend/next.config.js` configure le proxy :

```javascript
async rewrites() {
 return [
 {
 source: '/api/:path*',
 destination: 'http://127.0.0.1:8000/api/:path*',
 },
 ]
}
```

Les requêtes frontend `/api/*` sont automatiquement redirigées vers le backend.

### CORS (FastAPI)

Le backend autorise les origines suivantes :
- `http://localhost:3000` (Next.js)
- `http://localhost:5173` (Vite - si besoin)
- `http://localhost:3001` (alternative)

## Dépannage

### Backend ne démarre pas

```bash
# Vérifier que vous êtes dans le bon répertoire
cd /home/goamegah/Documents/develop/repo/adn/backend/orchestrator

# Vérifier l'environnement Python
which python
# Devrait pointer vers .venv/bin/python

# Réinstaller les dépendances
pip install -r ../requirements.txt
```

### Frontend ne se connecte pas au backend

1. Vérifier que le backend tourne sur le port 8000
2. Tester : `curl http://127.0.0.1:8000/health`
3. Vérifier les logs du terminal Next.js
4. Vider le cache du navigateur (Ctrl+Shift+R)

### Erreur CORS

Si vous voyez des erreurs CORS dans la console :
1. Vérifier que le backend a bien le middleware CORS
2. Redémarrer le backend
3. Vérifier l'URL dans `next.config.js`

### Erreur "Module not found"

```bash
# Frontend
cd next_frontend
rm -rf node_modules .next
npm install
npm run dev

# Backend
source .venv/bin/activate
pip install --upgrade -r requirements.txt
```

## Endpoints API

### GET `/`
Informations sur le service

### GET `/health`
Vérification de l'état du service

### POST `/api/analyze`
Analyse complète d'un patient

**Request:**
```json
{
 "patient_id": "PAT-2024-1847",
 "query": "Analyse patient avec dyspnée aiguë",
 "metadata": {}
}
```

**Response:**
```json
{
 "analysis_id": "ana_123456",
 "confidence": 0.87,
 "processing_time_ms": 1850,
 "patient_summary": { ... },
 "differentials": [ ... ],
 "alerts": [ ... ],
 "recommendations": [ ... ],
 "chat_reply": "..."
}
```

## Prochaines Étapes

1. **Intégration des agents réels** (actuellement en mode mock)
2. **Authentification utilisateur**
3. **Historique des analyses**
4. **Export PDF des rapports**
5. **Déploiement en production**

## Logs

### Backend
Les logs s'affichent dans le terminal où vous avez lancé `uvicorn`

### Frontend
Les logs s'affichent dans :
- Le terminal Next.js (server-side)
- La console du navigateur (client-side)

## Astuces

- **Hot Reload** : Les modifications sont automatiquement prises en compte
- **DevTools** : F12 pour ouvrir les outils de développement
- **Network Tab** : Voir les requêtes API en direct
- **Responsive Mode** : Tester mobile/tablet dans DevTools

---

** Votre stack ADN est maintenant opérationnelle !**

Pour toute question, consultez :
- `next_frontend/README.md` - Documentation frontend
- `next_frontend/IMPROVEMENTS.md` - Détails des améliorations UI
- `backend/orchestrator/main.py` - Code source backend
