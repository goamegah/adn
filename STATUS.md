# Application ADN - Prête à l'emploi !

## Statut Actuel

### Backend FastAPI
- **URL** : http://127.0.0.1:8000
- **Status** : RUNNING
- **Endpoints disponibles** :
 - `GET /` - Info service
 - `GET /health` - Health check
 - `POST /api/analyze` - Analyse patient

### Frontend Next.js
- **URL** : http://localhost:3000
- **Status** : RUNNING
- **Features** :
 - Interface responsive (mobile + desktop)
 - 4 panels agents IA
 - Chat interactif
 - Design moderne Tailwind

---

## Pour Démarrer l'Application

### Terminaux Actuellement Actifs

**Terminal 1 - Backend** : 
```bash
cd /home/goamegah/Documents/develop/repo/adn/backend/orchestrator
/home/goamegah/Documents/develop/repo/adn/.venv/bin/python -m uvicorn main:app --reload --port 8000
```

**Terminal 2 - Frontend** :
```bash
cd /home/goamegah/Documents/develop/repo/adn/next_frontend
npm run dev
```

### Si vous devez redémarrer

1. **Arrêter** : `Ctrl+C` dans chaque terminal
2. **Relancer** : Exécuter les commandes ci-dessus

---

## Comment Utiliser

### 1. Ouvrez votre navigateur
Allez sur : **http://localhost:3000**

### 2. Remplissez le formulaire
- **Patient ID** : `PAT-2024-1847`
- **Prompt** : `Analyse patient avec dyspnée aiguë`

### 3. Cliquez sur "Analyser avec ADN"

### 4. Consultez les résultats

L'interface affiche automatiquement :

 **Synthèse Patient** (coin haut gauche)
- Infos démographiques
- Antécédents
- Médicaments
- Signes vitaux

 **Diagnostics Différentiels** (coin haut droit)
- 3 hypothèses diagnostiques
- Probabilités colorées
- Barres de progression
- Actions suggérées

️ **Alertes Critiques** (coin bas gauche)
- Alertes de sévérité élevée
- Niveau de confiance

 **Recommandations** (coin bas droit)
- 4 recommandations priorisées
- Délais estimés

### 5. Utilisez le Chat

- Cliquez sur le bouton flottant (en bas à droite)
- Posez des questions
- Recevez des réponses de l'assistant

---

## Test Responsive

### Desktop
- Layout 2 colonnes
- Chat en modal centré
- Toutes les infos visibles

### Mobile
Pour tester sur mobile :
1. Ouvrez DevTools (F12)
2. Cliquez sur l'icône mobile/tablet
3. Sélectionnez un device (iPhone, iPad, etc.)

L'interface s'adapte automatiquement !

---

## Architecture

```
┌─────────────────────────────────────────┐
│ Frontend Next.js │
│ http://localhost:3000 │
│ │
│ ┌────────────────────────────────────┐ │
│ │ Components │ │
│ │ - PatientSynthesis │ │
│ │ - DiagnosticDifferentials │ │
│ │ - CriticalAlerts │ │
│ │ - ImmediateRecommendations │ │
│ │ - Chat │ │
│ └────────────────────────────────────┘ │
└─────────────────┬───────────────────────┘
 │
 │ HTTP POST /api/analyze
 │
┌─────────────────▼───────────────────────┐
│ Backend FastAPI │
│ http://127.0.0.1:8000 │
│ │
│ ┌────────────────────────────────────┐ │
│ │ Orchestrateur │ │
│ │ │ │
│ │ → Agent Synthétiseur │ │
│ │ → Agent Expert (Diagnostics) │ │
│ │ → Agent Critique (Alertes) │ │
│ │ → Agent Recommandations │ │
│ └────────────────────────────────────┘ │
└──────────────────────────────────────────┘
```

---

## Données de Test

Le backend retourne actuellement des données **mock** pour démonstration.

### Exemple de réponse API :

```json
{
 "analysis_id": "ana_654321",
 "confidence": 0.87,
 "processing_time_ms": 125,
 "patient_summary": {
 "patient": {
 "name": "Marie Dubois",
 "age": 65
 },
 "vital_signs": {
 "blood_pressure": {"systolic": 145, "diastolic": 92},
 "heart_rate": {"value": 110, "rhythm": "irrégulier"},
 "spo2": {"value": 89}
 }
 },
 "differentials": [
 {
 "pathology": "Embolie Pulmonaire",
 "probability_label": "Élevée",
 "score": 7.5,
 "evidence": [...]
 }
 ],
 "alerts": [...],
 "recommendations": [...]
}
```

---

## Personnalisation

### Modifier les couleurs (Frontend)

Éditez `next_frontend/app/globals.css` :

```css
:root {
 --bg: #0b1220; /* Fond principal */
 --accent: #6c5ce7; /* Couleur accent (bleu violet) */
}
```

### Modifier les données (Backend)

Éditez `backend/orchestrator/main.py` :
- Fonction `analyze()` ligne ~35

---

## Dépannage Rapide

### "Cannot connect to backend"
```bash
# Vérifier que le backend tourne
curl http://127.0.0.1:8000/health

# Si erreur, redémarrer le backend
cd backend/orchestrator
../../.venv/bin/python -m uvicorn main:app --reload --port 8000
```

### "Port 3000 already in use"
```bash
# Tuer le processus
lsof -ti:3000 | xargs kill -9

# Ou changer de port
npm run dev -- -p 3001
```

### "Module not found"
```bash
# Frontend
cd next_frontend
npm install

# Backend
cd backend
pip install -r requirements.txt
```

---

## Documentation

- **Frontend** : `next_frontend/README.md`
- **Améliorations UI** : `next_frontend/IMPROVEMENTS.md`
- **Guide complet** : `GETTING_STARTED.md`

---

## Prochaines Étapes

1. ~~Interface responsive~~
2. ~~Connexion Frontend-Backend~~
3. ~~Chat interactif~~
4. Intégration agents IA réels
5. Authentification
6. Historique des analyses
7. Export PDF
8. Déploiement production

---

## Commandes Utiles

```bash
# Vérifier le backend
curl http://127.0.0.1:8000/health

# Tester l'API
curl -X POST http://127.0.0.1:8000/api/analyze \
 -H "Content-Type: application/json" \
 -d '{"patient_id":"TEST","query":"test"}'

# Vérifier les processus
lsof -i :3000 # Frontend
lsof -i :8000 # Backend

# Logs en temps réel
# Backend : déjà visible dans le terminal
# Frontend : déjà visible dans le terminal + console navigateur (F12)
```

---

## Résumé

**Votre application ADN est maintenant complètement fonctionnelle !**

- Backend FastAPI opérationnel
- Frontend Next.js moderne et responsive
- Connexion API établie
- Interface utilisateur professionnelle
- Chat interactif
- 4 agents IA simulés

**Pour commencer** : Ouvrez http://localhost:3000 dans votre navigateur ! 

---

 **Date** : 18 octobre 2025 
‍ **Version** : 1.0.0 
 **Projet** : ADN - Agentic Diagnostic Navigator
