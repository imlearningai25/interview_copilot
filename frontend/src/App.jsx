import { useState, useCallback } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { jobsApi } from './api'
import JobCard from './components/JobCard'
import JobForm from './components/JobForm'
import SessionsModal from './components/SessionsModal'

const LAUNCHER_URL = import.meta.env.VITE_LAUNCHER_URL || 'http://localhost:4004'

function useToast() {
  const [toasts, setToasts] = useState([])
  const add = useCallback((msg, type = 'success') => {
    const id = Date.now()
    setToasts(t => [...t, { id, msg, type }])
    setTimeout(() => setToasts(t => t.filter(x => x.id !== id)), 4000)
  }, [])
  return { toasts, add }
}

export default function App() {
  const qc = useQueryClient()
  const { toasts, add: toast } = useToast()

  const [showForm,        setShowForm]        = useState(false)
  const [editingJob,      setEditingJob]      = useState(null)
  const [launching,       setLaunching]       = useState(false)
  const [sessionsJob,     setSessionsJob]     = useState(null)

  const { data: jobs = [], isLoading, isError } = useQuery({
    queryKey: ['jobs'],
    queryFn: jobsApi.list,
  })

  const invalidate = () => qc.invalidateQueries({ queryKey: ['jobs'] })

  const createMut = useMutation({
    mutationFn: jobsApi.create,
    onSuccess: () => { invalidate(); closeForm(); toast('Job created') },
    onError: e => toast(e.message, 'error'),
  })

  const updateMut = useMutation({
    mutationFn: ({ id, data }) => jobsApi.update(id, data),
    onSuccess: () => { invalidate(); closeForm(); toast('Job updated') },
    onError: e => toast(e.message, 'error'),
  })

  const deleteMut = useMutation({
    mutationFn: jobsApi.remove,
    onSuccess: () => { invalidate(); toast('Job deleted') },
    onError: e => toast(e.message, 'error'),
  })

  const activateMut = useMutation({
    mutationFn: jobsApi.activate,
    onSuccess: () => { invalidate(); toast('Active job updated') },
    onError: e => toast(e.message, 'error'),
  })

  const closeForm = () => { setShowForm(false); setEditingJob(null) }
  const handleSave = (data) => {
    if (editingJob) updateMut.mutate({ id: editingJob.id, data })
    else            createMut.mutate(data)
  }
  const handleEdit   = (job) => { setEditingJob(job); setShowForm(true) }
  const handleDelete = (id) => {
    if (!window.confirm('Delete this job configuration?')) return
    deleteMut.mutate(id)
  }

  const handleReady = async () => {
    setLaunching(true)
    try {
      const res = await fetch(`${LAUNCHER_URL}/launch`, { method: 'POST' })
      if (!res.ok) throw new Error('non-200')
      toast('Copilot is launching — watch for the overlay window')
    } catch {
      toast(
        'Launcher not running. Open a terminal and run: python launcher.py',
        'error'
      )
    } finally {
      setLaunching(false)
    }
  }

  const activeJob = jobs.find(j => j.is_active)

  return (
    <div>
      {/* ── Header ── */}
      <header className="header">
        <div className="header-inner">
          <div className="logo">🎯 Interview <span>Copilot</span></div>
          <button className="btn-primary" onClick={() => setShowForm(true)}>
            + New Job
          </button>
        </div>
      </header>

      <main className="main">
        {/* ── Toasts ── */}
        <div className="toast-wrap">
          {toasts.map(t => (
            <div key={t.id} className={`toast toast-${t.type}`}>
              {t.type === 'success' ? '✓' : '✕'} {t.msg}
            </div>
          ))}
        </div>

        {/* ── Active job banner ── */}
        {activeJob && (
          <div className="active-banner">
            <div className="active-banner-dot" />
            <div style={{ flex: 1 }}>
              <div className="active-banner-label">Active job</div>
              <div className="active-banner-role">{activeJob.role}</div>
              <div className="active-banner-meta">
                {activeJob.company}
                {activeJob.location && ` · ${activeJob.location}`}
              </div>
            </div>
            <button
              className="btn-ready"
              onClick={handleReady}
              disabled={launching}
            >
              {launching ? 'Launching…' : 'Ready'}
            </button>
          </div>
        )}

        {/* ── Section header ── */}
        <div className="section-row">
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <span className="section-title">Saved Jobs</span>
            <span className="count-badge">{jobs.length}</span>
          </div>
        </div>

        {/* ── States ── */}
        {isLoading && (
          <div className="state-center">
            <div className="state-icon">⏳</div>
            <div>Loading jobs…</div>
          </div>
        )}
        {isError && (
          <div className="state-center state-error">
            <div className="state-icon">⚠️</div>
            <div>Could not reach the API. Is the backend running?</div>
          </div>
        )}
        {!isLoading && !isError && jobs.length === 0 && (
          <div className="state-center">
            <div className="state-icon">📋</div>
            <div>No job configurations yet.</div>
            <button className="btn-primary" style={{ marginTop: 20 }}
              onClick={() => setShowForm(true)}>
              Add your first job
            </button>
          </div>
        )}

        {/* ── Job list ── */}
        <div className="job-grid">
          {jobs.map(job => (
            <JobCard
              key={job.id}
              job={job}
              onEdit={handleEdit}
              onDelete={handleDelete}
              onActivate={id => activateMut.mutate(id)}
              onSessions={setSessionsJob}
            />
          ))}
        </div>
      </main>

      {/* ── Job form modal ── */}
      {showForm && (
        <div className="overlay" onClick={e => e.target === e.currentTarget && closeForm()}>
          <div className="modal">
            <JobForm
              job={editingJob}
              onSave={handleSave}
              onClose={closeForm}
            />
          </div>
        </div>
      )}

      {/* ── Sessions modal ── */}
      {sessionsJob && (
        <SessionsModal
          job={sessionsJob}
          onClose={() => setSessionsJob(null)}
          onToast={toast}
        />
      )}
    </div>
  )
}
