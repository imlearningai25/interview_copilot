import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { sessionsApi } from '../api'

function fmt(iso) {
  return new Date(iso).toLocaleString('en-US', {
    month: 'short', day: 'numeric', year: 'numeric',
    hour: 'numeric', minute: '2-digit',
  })
}

function SessionRow({ summary, checked, onCheck }) {
  const [open, setOpen] = useState(false)

  const { data: session, isLoading } = useQuery({
    queryKey: ['session', summary.id],
    queryFn: () => sessionsApi.get(summary.id),
    enabled: open,
  })

  return (
    <div className={`session-row${open ? ' open' : ''}`}>
      <div className="session-header">
        <input
          type="checkbox"
          className="session-checkbox"
          checked={checked}
          onChange={e => onCheck(summary.id, e.target.checked)}
          onClick={e => e.stopPropagation()}
        />
        <button className="session-header-btn" onClick={() => setOpen(o => !o)}>
          <div>
            <div className="session-date">{fmt(summary.started_at)}</div>
            <div className="session-meta">
              {summary.entry_count} question{summary.entry_count !== 1 ? 's' : ''}
              {summary.ended_at ? '' : ' · in progress'}
            </div>
          </div>
          <span className="session-chevron">{open ? '▲' : '▼'}</span>
        </button>
      </div>

      {open && (
        <div className="session-body">
          {isLoading && <div className="session-loading">Loading…</div>}
          {session && session.entries.length === 0 && (
            <div className="session-empty">No questions answered in this session.</div>
          )}
          {session && session.entries.map(entry => (
            <div key={entry.id} className="qa-entry">
              <div className="qa-time">{fmt(entry.asked_at)}</div>
              <div className="qa-question">{entry.question}</div>
              <div className="qa-answer">{entry.answer}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default function SessionsModal({ job, onClose, onToast }) {
  const qc = useQueryClient()
  const [selected, setSelected] = useState(new Set())

  const { data: sessions = [], isLoading } = useQuery({
    queryKey: ['sessions', job.id],
    queryFn: () => sessionsApi.list(job.id),
  })

  const invalidate = () => {
    qc.invalidateQueries({ queryKey: ['sessions', job.id] })
    setSelected(new Set())
  }

  const deleteMut = useMutation({
    mutationFn: (ids) => ids.length === 1
      ? sessionsApi.remove(ids[0])
      : sessionsApi.bulkRemove(ids),
    onSuccess: (_, ids) => {
      invalidate()
      onToast(`${ids.length} session${ids.length !== 1 ? 's' : ''} deleted`)
    },
    onError: e => onToast(e.message, 'error'),
  })

  const handleCheck = (id, checked) => {
    setSelected(prev => {
      const next = new Set(prev)
      checked ? next.add(id) : next.delete(id)
      return next
    })
  }

  const allChecked = sessions.length > 0 && selected.size === sessions.length
  const toggleAll = () => setSelected(allChecked ? new Set() : new Set(sessions.map(s => s.id)))

  const handleDelete = () => {
    const ids = [...selected]
    if (!window.confirm(`Delete ${ids.length} session${ids.length !== 1 ? 's' : ''}? This cannot be undone.`)) return
    deleteMut.mutate(ids)
  }

  return (
    <div className="overlay" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="modal sessions-modal">
        <div className="form-header">
          <div>
            <h3>Interview Sessions</h3>
            <div style={{ fontSize: 13, color: 'var(--muted)', marginTop: 2 }}>
              {job.role} · {job.company}
            </div>
          </div>
          <button className="btn-close" onClick={onClose}>✕</button>
        </div>

        {sessions.length > 0 && (
          <div className="sessions-toolbar">
            <label className="sessions-select-all">
              <input type="checkbox" checked={allChecked} onChange={toggleAll} />
              <span>Select all</span>
            </label>
            {selected.size > 0 && (
              <button
                className="btn-sm btn-delete"
                onClick={handleDelete}
                disabled={deleteMut.isPending}
              >
                {deleteMut.isPending ? 'Deleting…' : `Delete (${selected.size})`}
              </button>
            )}
          </div>
        )}

        <div className="sessions-list">
          {isLoading && <div className="session-loading">Loading sessions…</div>}
          {!isLoading && sessions.length === 0 && (
            <div className="session-empty">
              No sessions yet. Start the copilot with this job active to record a session.
            </div>
          )}
          {sessions.map(s => (
            <SessionRow
              key={s.id}
              summary={s}
              checked={selected.has(s.id)}
              onCheck={handleCheck}
            />
          ))}
        </div>
      </div>
    </div>
  )
}
