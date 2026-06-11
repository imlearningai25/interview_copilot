import { useState } from 'react'

export default function JobForm({ job, onSave, onClose }) {
  const [form, setForm] = useState({
    role:            job?.role             || '',
    company:         job?.company          || '',
    location:        job?.location         || '',
    job_description: job?.job_description  || '',
  })
  const [errors, setErrors]   = useState({})
  const [saving, setSaving]   = useState(false)

  const set = (k, v) => {
    setForm(f => ({ ...f, [k]: v }))
    setErrors(e => ({ ...e, [k]: undefined }))
  }

  const validate = () => {
    const e = {}
    if (!form.role.trim())    e.role    = 'Required'
    if (!form.company.trim()) e.company = 'Required'
    return e
  }

  const submit = async (ev) => {
    ev.preventDefault()
    const e = validate()
    if (Object.keys(e).length) { setErrors(e); return }
    setSaving(true)
    try {
      await onSave(form)
    } finally {
      setSaving(false)
    }
  }

  return (
    <>
      <div className="form-header">
        <h3>{job ? 'Edit Job' : 'New Job'}</h3>
        <button className="btn-close" onClick={onClose} aria-label="Close">✕</button>
      </div>

      <form onSubmit={submit}>
        <div className="form-body">
          <div className="field">
            <label>Job Title / Role <span className="req">*</span></label>
            <input
              value={form.role}
              onChange={e => set('role', e.target.value)}
              placeholder="e.g. Principal Software Engineer"
              autoFocus
            />
            {errors.role && <div className="field-error">{errors.role}</div>}
          </div>

          <div className="row-2">
            <div className="field">
              <label>Company <span className="req">*</span></label>
              <input
                value={form.company}
                onChange={e => set('company', e.target.value)}
                placeholder="e.g. Google"
              />
              {errors.company && <div className="field-error">{errors.company}</div>}
            </div>
            <div className="field">
              <label>Location</label>
              <input
                value={form.location}
                onChange={e => set('location', e.target.value)}
                placeholder="e.g. New York, NY / Remote"
              />
            </div>
          </div>

          <div className="field">
            <label>Job Description</label>
            <textarea
              value={form.job_description}
              onChange={e => set('job_description', e.target.value)}
              placeholder="Paste the full job description here — responsibilities, required skills, qualifications…"
              rows={10}
            />
            <div className="field-hint">
              Tip: paste the entire JD. The copilot will surface the most relevant parts of your background for each question.
            </div>
          </div>
        </div>

        <div className="form-footer">
          <button type="button" className="btn-ghost" onClick={onClose}>Cancel</button>
          <button type="submit" className="btn-primary" disabled={saving}>
            {saving ? 'Saving…' : (job ? 'Save Changes' : 'Create Job')}
          </button>
        </div>
      </form>
    </>
  )
}
