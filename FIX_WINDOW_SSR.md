# Fix: window is not defined (Next.js SSR)

## **Problème**

```bash
⨯ ReferenceError: window is not defined
 at Home (./app/page.js:203:35)
> 203 | {(view === 'results' || window.innerWidth >= 1024) && (
```

**Cause:** `window` n'existe pas côté serveur (Server-Side Rendering)

---

## **Solution**

### **1. Ajout d'un état `isDesktop`**
```jsx
const [isDesktop, setIsDesktop] = useState(false)
```

### **2. Détection côté client avec `useEffect`**
```jsx
useEffect(() => {
 const checkDesktop = () => setIsDesktop(window.innerWidth >= 1024)
 checkDesktop()
 window.addEventListener('resize', checkDesktop)
 return () => window.removeEventListener('resize', checkDesktop)
}, [])
```

### **3. Remplacement des conditions**
```jsx
// Avant
{(view === 'chat' || window.innerWidth >= 1024) && (

// Après
{(view === 'chat' || isDesktop) && (
```

### **4. Check sécurisé dans handleChatMessage**
```jsx
// Avant
if (window.innerWidth < 1024) {

// Après
if (typeof window !== 'undefined' && window.innerWidth < 1024) {
```

---

## **Résultat**

- Plus d'erreur SSR
- Détection responsive qui fonctionne
- Resize listener pour adaptation dynamique
- Compatible Next.js 14

---

## **Status**

**Backend:** http://127.0.0.1:8000 
**Frontend:** http://localhost:3001 

**Tout fonctionne !** 
