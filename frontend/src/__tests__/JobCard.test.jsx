import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import JobCard from '../components/JobCard'

const BASE_JOB = {
  id: 1,
  role: 'Principal Engineer',
  company: 'Acme Corp',
  location: 'New York, NY',
  job_description: 'Build great products.',
  is_active: false,
  created_at: '2024-06-01T12:00:00Z',
}

function setup(jobOverrides = {}, handlers = {}) {
  const props = {
    job: { ...BASE_JOB, ...jobOverrides },
    onEdit: vi.fn(),
    onDelete: vi.fn(),
    onActivate: vi.fn(),
    ...handlers,
  }
  render(<JobCard {...props} />)
  return props
}

describe('JobCard — display', () => {
  it('renders role and company', () => {
    setup()
    expect(screen.getByText('Principal Engineer')).toBeInTheDocument()
    expect(screen.getByText('Acme Corp')).toBeInTheDocument()
  })

  it('renders location', () => {
    setup()
    expect(screen.getByText(/New York, NY/)).toBeInTheDocument()
  })

  it('renders a description preview', () => {
    setup()
    expect(screen.getByText(/Build great products/)).toBeInTheDocument()
  })

  it('omits location when null', () => {
    setup({ location: null })
    expect(screen.queryByText(/New York/)).not.toBeInTheDocument()
  })

  it('omits description preview when null', () => {
    setup({ job_description: null })
    expect(screen.queryByText(/Build great/)).not.toBeInTheDocument()
  })
})

describe('JobCard — active state', () => {
  it('shows "Active" pill when active', () => {
    setup({ is_active: true })
    expect(screen.getByText('Active')).toBeInTheDocument()
  })

  it('hides "Active" pill when not active', () => {
    setup({ is_active: false })
    expect(screen.queryByText('Active')).not.toBeInTheDocument()
  })

  it('shows "Set Active" button when not active', () => {
    setup({ is_active: false })
    expect(screen.getByRole('button', { name: 'Set Active' })).toBeInTheDocument()
  })

  it('hides "Set Active" button when already active', () => {
    setup({ is_active: true })
    expect(screen.queryByRole('button', { name: 'Set Active' })).not.toBeInTheDocument()
  })
})

describe('JobCard — callbacks', () => {
  it('calls onActivate with job id', async () => {
    const user = userEvent.setup()
    const { onActivate } = setup({ is_active: false })
    await user.click(screen.getByRole('button', { name: 'Set Active' }))
    expect(onActivate).toHaveBeenCalledWith(BASE_JOB.id)
  })

  it('calls onEdit with full job object', async () => {
    const user = userEvent.setup()
    const { onEdit } = setup()
    await user.click(screen.getByRole('button', { name: 'Edit' }))
    expect(onEdit).toHaveBeenCalledWith(expect.objectContaining({ id: BASE_JOB.id }))
  })

  it('calls onDelete with job id', async () => {
    const user = userEvent.setup()
    const { onDelete } = setup()
    await user.click(screen.getByRole('button', { name: 'Delete' }))
    expect(onDelete).toHaveBeenCalledWith(BASE_JOB.id)
  })
})
