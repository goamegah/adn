# Vue Mobile ADN Pro

## Design Mobile Actuel vs Amélioré

### **Architecture Mobile Proposée**

Sur mobile, le Split View (40/60) ne fonctionne pas bien. Voici l'approche optimale :

---

## **Layout Mobile Adaptatif**

### **< 768px (Mobile/Tablet)**
```
┌─────────────────────────┐
│ ADN Pro [●] │ ← Header compact
├─────────────────────────┤
│ │
│ CHAT FULLSCREEN │ ← Chat prend tout l'écran
│ │
│ [Messages...] │
│ │
│ [Input + Send] │
│ │
└─────────────────────────┘
 ↓ User envoie message
┌─────────────────────────┐
│ < Retour Résultats │ ← Navigation
├─────────────────────────┤
│ PANELS FULLSCREEN │ ← Panels en scroll vertical
│ │
│ ┌───────────────────┐ │
│ │ Synthèse │ │
│ └───────────────────┘ │
│ ┌───────────────────┐ │
│ │ Diagnostics │ │
│ └───────────────────┘ │
│ ┌───────────────────┐ │
│ │ ️ Alertes │ │
│ └───────────────────┘ │
│ ┌───────────────────┐ │
│ │ Recommandations│ │
│ └───────────────────┘ │
│ │
│ [ Retour au chat] │ ← Bouton flottant
└─────────────────────────┘
```

### **≥ 768px (Desktop)**
```
┌────────────────────────────────────┐
│ ADN Pro [●] Active │
├────────────┬───────────────────────┤
│ CHAT 40% │ RESULTS 60% │
│ │ │
│ [Msgs] │ [Panels scrollable] │
│ │ │
└────────────┴───────────────────────┘
```

---

## **Fonctionnalités Mobile**

### **1. Navigation Tabs**
```jsx
[ Chat] [ Résultats] [ Stats]
 ^^^^ Actif
```

### **2. Gestes**
- **Swipe gauche/droite** : Basculer Chat ↔ Résultats
- **Pull to refresh** : Recharger l'analyse
- **Long press** : Copier un message

### **3. Bottom Sheet**
```
┌─────────────────────────┐
│ [Chat Messages] │
│ │
│ ═══════════════════ │ ← Drag handle
│ ┌─────────────────┐ │
│ │ Synthèse │ │ ← Bottom sheet modal
│ │ [Preview...] │ │
│ └─────────────────┘ │
└─────────────────────────┘
```

### **4. Compact Cards**
Les panels sont condensés sur mobile :
```jsx
// Desktop: Verbose
<div className="p-6">
 <h3 className="text-xl">Synthèse Patient</h3>
 <p className="text-base">...</p>
</div>

// Mobile: Compact
<div className="p-3">
 <h3 className="text-sm font-semibold">Synthèse</h3>
 <p className="text-xs">...</p>
</div>
```

---

## **Approches Possibles**

### **Option A : Tabs (Simple)**
Deux onglets : Chat | Résultats

**Avantages :**
- Simple à implémenter
- Familier pour les utilisateurs
- Pas de confusion

**Inconvénients :**
- Pas de vue simultanée
- Nécessite des switches

### **Option B : Bottom Drawer (Moderne)**
Chat en fullscreen, results en tiroir du bas

**Avantages :**
- UX moderne (style Google Maps)
- Chat toujours accessible
- Preview des résultats visible

**Inconvénients :**
- Plus complexe
- Peut cacher du contenu

### **Option C : Stack avec FAB (Recommandé)**
Vue principale = Chat, FAB "Voir résultats" qui slide les panels

**Avantages :**
- Chat priorité
- Résultats accessibles rapidement
- Pas de navigation compliquée

---

## **Implémentation Recommandée**

Je propose **Option C + Tabs** :

### **Mobile Flow:**
```
1. User arrive → Chat fullscreen
2. User pose question → Loading indicator
3. Notification: "Résultats prêts " 
4. Badge sur onglet [Résultats (4)]
5. User swipe/tap → Panels fullscreen
6. FAB pour retour rapide au chat
```

### **Code Structure:**
```jsx
// Mobile: Stack Navigation
<div className="lg:flex lg:flex-row">
 {/* Mobile: Conditional Rendering */}
 <div className={`
 ${view === 'chat' ? 'block' : 'hidden lg:block'}
 lg:w-2/5
 `}>
 <ChatPro />
 </div>

 <div className={`
 ${view === 'results' ? 'block' : 'hidden lg:block'}
 lg:w-3/5
 `}>
 <Results />
 </div>

 {/* Mobile Navigation Tabs */}
 <MobileTabBar 
 active={view}
 onSwitch={setView}
 className="lg:hidden"
 />
</div>
```

---

## **Design Mobile Détaillé**

### **Header Mobile**
```jsx
<header className="sticky top-0 z-50 bg-slate-900/95 backdrop-blur">
 <div className="flex items-center justify-between px-4 py-3">
 <div className="flex items-center gap-2">
 <Brain className="w-6 h-6" />
 <span className="font-bold text-sm">ADN</span>
 </div>
 
 {/* Status dot */}
 <div className="flex items-center gap-2">
 <span className="w-2 h-2 bg-green-400 rounded-full"></span>
 <span className="text-xs text-slate-400">Actif</span>
 </div>
 </div>
 
 {/* Tabs */}
 <div className="flex border-t border-slate-700">
 <button className="flex-1 py-3 text-sm">
 Chat
 </button>
 <button className="flex-1 py-3 text-sm border-l border-slate-700">
 Résultats {badge}
 </button>
 </div>
</header>
```

### **Chat Mobile**
```jsx
<div className="h-[calc(100vh-120px)] flex flex-col">
 {/* Messages */}
 <div className="flex-1 overflow-y-auto px-3 py-2">
 <Message compact />
 </div>
 
 {/* Input - Compact */}
 <div className="p-3 bg-slate-900">
 <div className="flex gap-2">
 <input 
 className="flex-1 text-sm py-2 px-3"
 placeholder="Message..."
 />
 <button className="w-10 h-10">
 <Send />
 </button>
 </div>
 </div>
</div>
```

### **Panels Mobile**
```jsx
<div className="overflow-y-auto px-3 py-4 space-y-3">
 {/* Compact Cards */}
 <Card className="p-3">
 <h3 className="text-sm font-semibold mb-2"> Synthèse</h3>
 <div className="text-xs space-y-1">
 {/* Données condensées */}
 </div>
 </Card>
</div>
```

### **FAB (Floating Action Button)**
```jsx
{/* Visible seulement sur mobile dans vue Results */}
<button className="
 lg:hidden
 fixed bottom-4 right-4 z-50
 w-14 h-14
 bg-blue-600 rounded-full
 shadow-lg shadow-blue-500/50
 flex items-center justify-center
" onClick={() => setView('chat')}>
 <MessageCircle className="w-6 h-6" />
</button>
```

---

## **Responsive Breakpoints**

```css
/* Mobile First */
.container {
 /* < 640px : Stack vertical */
 flex-direction: column;
}

/* Tablet : 768px+ */
@media (min-width: 768px) {
 .container {
 /* Tabs horizontaux ou small split */
 }
}

/* Desktop : 1024px+ */
@media (min-width: 1024px) {
 .container {
 /* Split view 40/60 */
 flex-direction: row;
 }
}
```

---

## **Animation Mobile**

### **Transitions entre vues**
```jsx
import { motion, AnimatePresence } from 'framer-motion'

<AnimatePresence mode="wait">
 {view === 'chat' && (
 <motion.div
 initial={{ x: -100, opacity: 0 }}
 animate={{ x: 0, opacity: 1 }}
 exit={{ x: -100, opacity: 0 }}
 transition={{ duration: 0.2 }}
 >
 <ChatPro />
 </motion.div>
 )}
 
 {view === 'results' && (
 <motion.div
 initial={{ x: 100, opacity: 0 }}
 animate={{ x: 0, opacity: 1 }}
 exit={{ x: 100, opacity: 0 }}
 transition={{ duration: 0.2 }}
 >
 <Results />
 </motion.div>
 )}
</AnimatePresence>
```

---

## **Voulez-vous que je l'implémente ?**

Je peux créer :

**Version 1 : Tabs Simple** (15 min)
- Deux onglets : Chat | Résultats
- Switch instantané
- FAB pour navigation rapide

**Version 2 : Bottom Drawer** (30 min)
- Chat fullscreen
- Drawer tiroir du bas pour résultats
- Drag to expand

**Version 3 : Hybrid Pro** (45 min)
- Tabs mobile
- Split view desktop (déjà fait)
- Swipe gestures
- Animations fluides

**Laquelle préférez-vous ?** 
