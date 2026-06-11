/**
 * Tests for jobsApi (src/api.js).
 *
 * VITE_API_URL is not set in the test environment, so BASE resolves to ''
 * and all request paths are relative (e.g. /api/jobs).
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { jobsApi } from '../api'

const MOCK_JOB = {
  id: 1,
  role: 'Principal Engineer',
  company: 'Acme Corp',
  location: 'Remote',
  job_description: null,
  is_active: false,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: null,
}

function stubFetch(data, status = 200) {
  return vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
    ok: status < 400,
    status,
    json: () => Promise.resolve(data),
  }))
}

afterEach(() => vi.unstubAllGlobals())

describe('jobsApi.list', () => {
  it('GETs /api/jobs', async () => {
    stubFetch([MOCK_JOB])
    const result = await jobsApi.list()
    expect(fetch).toHaveBeenCalledWith('/api/jobs', expect.any(Object))
    expect(result).toEqual([MOCK_JOB])
  })
})

describe('jobsApi.get', () => {
  it('GETs /api/jobs/:id', async () => {
    stubFetch(MOCK_JOB)
    await jobsApi.get(1)
    expect(fetch).toHaveBeenCalledWith('/api/jobs/1', expect.any(Object))
  })
})

describe('jobsApi.active', () => {
  it('GETs /api/jobs/active', async () => {
    stubFetch(MOCK_JOB)
    await jobsApi.active()
    expect(fetch).toHaveBeenCalledWith('/api/jobs/active', expect.any(Object))
  })
})

describe('jobsApi.create', () => {
  it('POSTs to /api/jobs with JSON body', async () => {
    stubFetch(MOCK_JOB, 201)
    const payload = { role: 'SWE', company: 'Acme' }
    await jobsApi.create(payload)
    expect(fetch).toHaveBeenCalledWith(
      '/api/jobs',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify(payload),
      }),
    )
  })
})

describe('jobsApi.update', () => {
  it('PUTs to /api/jobs/:id with JSON body', async () => {
    stubFetch(MOCK_JOB)
    const payload = { role: 'Staff Engineer' }
    await jobsApi.update(1, payload)
    expect(fetch).toHaveBeenCalledWith(
      '/api/jobs/1',
      expect.objectContaining({
        method: 'PUT',
        body: JSON.stringify(payload),
      }),
    )
  })
})

describe('jobsApi.remove', () => {
  it('DELETEs /api/jobs/:id', async () => {
    stubFetch(null, 204)
    await jobsApi.remove(1)
    expect(fetch).toHaveBeenCalledWith(
      '/api/jobs/1',
      expect.objectContaining({ method: 'DELETE' }),
    )
  })

  it('returns null for 204 No Content', async () => {
    stubFetch(null, 204)
    const result = await jobsApi.remove(1)
    expect(result).toBeNull()
  })
})

describe('jobsApi.activate', () => {
  it('PATCHes /api/jobs/:id/activate', async () => {
    stubFetch({ ...MOCK_JOB, is_active: true })
    await jobsApi.activate(1)
    expect(fetch).toHaveBeenCalledWith(
      '/api/jobs/1/activate',
      expect.objectContaining({ method: 'PATCH' }),
    )
  })
})

describe('error handling', () => {
  it('throws with detail message on non-ok response', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: false,
      status: 404,
      json: () => Promise.resolve({ detail: 'Job not found' }),
    }))
    await expect(jobsApi.get(99)).rejects.toThrow('Job not found')
  })

  it('falls back to statusText when response has no detail', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: false,
      status: 500,
      statusText: 'Internal Server Error',
      json: () => Promise.reject(new Error('not json')),
    }))
    await expect(jobsApi.list()).rejects.toThrow('Internal Server Error')
  })
})
