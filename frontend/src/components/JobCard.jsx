export default function JobCard({ job, onEdit, onDelete, onActivate }) {
  const preview = job.job_description
    ? job.job_description.slice(0, 160) + (job.job_description.length > 160 ? '…' : '')
    : null

  const date = new Date(job.created_at).toLocaleDateString('en-US', {
    month: 'short', day: 'numeric', year: 'numeric',
  })

  return (
    <div className={`job-card${job.is_active ? ' active' : ''}`}>
      {job.is_active && <div className="active-pill">Active</div>}

      <div className="job-role">{job.role}</div>
      <div className="job-company">{job.company}</div>
      {job.location && <div className="job-location">📍 {job.location}</div>}
      {preview && <div className="job-desc">{preview}</div>}

      <div className="card-footer">
        <span className="card-date">{date}</span>
        <div className="card-actions">
          {!job.is_active && (
            <button className="btn-sm btn-activate" onClick={() => onActivate(job.id)}>
              Set Active
            </button>
          )}
          <button className="btn-sm btn-edit" onClick={() => onEdit(job)}>Edit</button>
          <button className="btn-sm btn-delete" onClick={() => onDelete(job.id)}>Delete</button>
        </div>
      </div>
    </div>
  )
}
