// frontend/src/lib/api.js
export async function analyze(patientId, query) {
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), 180000) // 3 minutes
  
  try {
    const payload = { patient_id: patientId, query }
    const res = await fetch('/api/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      signal: controller.signal
    })
    
    clearTimeout(timeoutId)
    
    if (!res.ok) {
      const text = await res.text()
      throw new Error(`Server ${res.status}: ${text}`)
    }
    
    return await res.json()
    
  } catch (error) {
    clearTimeout(timeoutId)
    
    if (error.name === 'AbortError') {
      throw new Error('⏱️ Analyse trop longue (>3min). Réessayez.')
    }
    
    throw error
  }
}