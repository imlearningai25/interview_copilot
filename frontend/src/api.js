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
