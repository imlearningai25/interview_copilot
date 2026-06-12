const BASE = import.meta.env.VITE_API_URL || ''

async function req(path, opts = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...opts.headers },
    ...opts,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || `HTTP ${res.status}`)
  }
  return res.status === 204 ? null : res.json()
}

export const jobsApi = {
  list:     ()         => req('/api/jobs'),
  get:      (id)       => req(`/api/jobs/${id}`),
  active:   ()         => req('/api/jobs/active'),
  create:   (data)     => req('/api/jobs',        { method: 'POST',  body: JSON.stringify(data) }),
  update:   (id, data) => req(`/api/jobs/${id}`,  { method: 'PUT',   body: JSON.stringify(data) }),
  remove:   (id)       => req(`/api/jobs/${id}`,  { method: 'DELETE' }),
  activate: (id)       => req(`/api/jobs/${id}/activate`, { method: 'PATCH' }),
}

export const sessionsApi = {
  list:       (jobId)  => req(`/api/sessions?job_id=${jobId}`),
  get:        (id)     => req(`/api/sessions/${id}`),
  create:     (jobId)  => req('/api/sessions', { method: 'POST', body: JSON.stringify({ job_id: jobId }) }),
  end:        (id)     => req(`/api/sessions/${id}/end`, { method: 'PATCH' }),
  remove:     (id)     => req(`/api/sessions/${id}`, { method: 'DELETE' }),
  bulkRemove: (ids)    => req('/api/sessions', { method: 'DELETE', body: JSON.stringify({ ids }) }),
  addEntry:   (id, data) => req(`/api/sessions/${id}/entries`, { method: 'POST', body: JSON.stringify(data) }),
}
