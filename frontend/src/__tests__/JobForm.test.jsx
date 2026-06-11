import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import JobForm from '../components/JobForm'

const EXISTING_JOB = {
  id: 1,
  role: 'Staff Engineer',
  company: 'Google',
  location: 'Remote',
  job_description: 'Work on search.',
}

function setup(job = null, onSave = vi.fn(), onClose = vi.fn()) {
  render(<JobForm job={job} onSave={onSave} onClose={onClose} />)
  return { onSave, onClose }
}

describe('JobForm — rendering', () => {
  it('shows "New Job" heading for a new job', () => {
    setup(null)
    expect(screen.getByText('New Job')).toBeInTheDocument()
  })

  it('shows "Edit Job" heading when editing', () => {
    setup(EXISTING_JOB)
    expect(screen.getByText('Edit Job')).toBeInTheDocument()
  })

  it('pre-fills role and company when editing', () => {
    setup(EXISTING_JOB)
    expect(screen.getByDisplayValue('Staff Engineer')).toBeInTheDocument()
    expect(screen.getByDisplayValue('Google')).toBeInTheDocument()
  })

  it('renders empty inputs for a new job', () => {
    setup(null)
    expect(screen.getByPlaceholderText(/Principal Software Engineer/i).value).toBe('')
    expect(screen.getByPlaceholderText(/Google/i).value).toBe('')
  })

  it('shows "Create Job" submit button for new job', () => {
    setup(null)
    expect(screen.getByRole('button', { name: 'Create Job' })).toBeInTheDocument()
  })

  it('shows "Save Changes" submit button when editing', () => {
    setup(EXISTING_JOB)
    expect(screen.getByRole('button', { name: 'Save Changes' })).toBeInTheDocument()
  })
})

describe('JobForm — validation', () => {
  it('shows "Required" error when role is empty on submit', async () => {
    const user = userEvent.setup()
    setup(null)
    await user.click(screen.getByRole('button', { name: 'Create Job' }))
    expect(screen.getAllByText('Required').length).toBeGreaterThanOrEqual(1)
  })

  it('shows "Required" error when company is empty on submit', async () => {
    const user = userEvent.setup()
    setup(null)
    await user.type(screen.getByPlaceholderText(/Principal Software Engineer/i), 'SWE')
    await user.click(screen.getByRole('button', { name: 'Create Job' }))
    expect(screen.getByText('Required')).toBeInTheDocument()
  })

  it('clears field error when user starts typing', async () => {
    const user = userEvent.setup()
    setup(null)
    await user.click(screen.getByRole('button', { name: 'Create Job' }))
    expect(screen.getAllByText('Required').length).toBeGreaterThan(0)
    await user.type(screen.getByPlaceholderText(/Principal Software Engineer/i), 'E')
    const errors = screen.queryAllByText('Required')
    expect(errors.length).toBeLessThan(2)
  })
})

describe('JobForm — submission', () => {
  it('calls onSave with form data when valid', async () => {
    const user = userEvent.setup()
    const { onSave } = setup(null)
    await user.type(screen.getByPlaceholderText(/Principal Software Engineer/i), 'SWE')
    await user.type(screen.getByPlaceholderText(/Google/i), 'Acme')
    await user.click(screen.getByRole('button', { name: 'Create Job' }))
    expect(onSave).toHaveBeenCalledWith(
      expect.objectContaining({ role: 'SWE', company: 'Acme' }),
    )
  })

  it('does not call onSave when validation fails', async () => {
    const user = userEvent.setup()
    const { onSave } = setup(null)
    await user.click(screen.getByRole('button', { name: 'Create Job' }))
    expect(onSave).not.toHaveBeenCalled()
  })
})

describe('JobForm — close', () => {
  it('calls onClose when Cancel is clicked', async () => {
    const user = userEvent.setup()
    const { onClose } = setup(null)
    await user.click(screen.getByRole('button', { name: 'Cancel' }))
    expect(onClose).toHaveBeenCalled()
  })

  it('calls onClose when ✕ button is clicked', async () => {
    const user = userEvent.setup()
    const { onClose } = setup(null)
    await user.click(screen.getByLabelText('Close'))
    expect(onClose).toHaveBeenCalled()
  })
})
