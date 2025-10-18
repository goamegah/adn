# ADN - Next.js Frontend

**Application Next.js moderne et responsive** pour le système ADN (Agentic Diagnostic Navigator).

## Fonctionnalités

- Interface **responsive** (mobile, tablet, desktop)
- Design **moderne** avec Tailwind CSS
- **4 agents IA** : Synthétiseur, Expert, Critique, Recommandations
- Chat intégré avec modal
- Animations fluides
- Dark mode natif

## Démarrage Rapide

### 1. Installer les dépendances
```bash
npm install
```

### 2. Lancer le serveur de développement
```bash
npm run dev
```

### 3. Ouvrir l'application
Accédez à [http://localhost:3000](http://localhost:3000)

## Prérequis

**Backend FastAPI** doit être lancé sur `http://127.0.0.1:8000`

```bash
# Dans un autre terminal
cd ../backend/orchestrator
source ../../.venv/bin/activate # ou équivalent Windows
uvicorn main:app --reload --port 8000
```

## Structure

```
next_frontend/
├── app/
│ ├── layout.js # Layout racine
│ ├── page.js # Page principale (responsive)
│ └── globals.css # Styles Tailwind + animations
├── components/
│ ├── icons.jsx # Icônes SVG personnalisées
│ ├── PanelsNew.jsx # Composants de dashboard
│ └── Chat.jsx # Interface de chat
├── lib/
│ └── api.js # Fonctions API
└── next.config.js # Config Next.js (proxy API)
```

## Améliorations UI/UX

Voir [IMPROVEMENTS.md](./IMPROVEMENTS.md) pour la liste complète des améliorations.

**Highlights** :
- Mobile-first design
- Badges colorés pour les probabilités
- Barres de progression animées
- Chat modal avec overlay
- Animations fluides

## ️ Technologies

- **Next.js 14** - Framework React
- **Tailwind CSS 3** - Styling
- **React 18** - UI Library
- **FastAPI** - Backend (proxy via Next.js)

## Scripts

```bash
npm run dev # Développement (port 3000)
npm run build # Build production
npm run start # Serveur production
npm run lint # Linter ESLint
```

## API Proxy

Les requêtes `/api/*` sont automatiquement proxifiées vers `http://127.0.0.1:8000/api/*` (configuré dans `next.config.js`).

## Responsive Breakpoints

- **Mobile**: < 640px
- **Tablet**: 640px - 1024px 
- **Desktop**: > 1024px

## Prochaines Étapes

- [ ] Ajouter l'authentification
- [ ] Implémenter le SSR pour le SEO
- [ ] Ajouter des tests (Jest + React Testing Library)
- [ ] Déployer sur Vercel

## Licence

Prototype - ADN © 2024

