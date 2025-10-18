// API helper to call the FastAPI orchestrator
export async function analyze(patientId, query) {
  const payload = { patient_id: patientId, query }
  const res = await fetch('/api/analyze', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`Server ${res.status}: ${text}`)
  }
  return await res.json()
}
