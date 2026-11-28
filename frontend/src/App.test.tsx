import '@testing-library/jest-dom/vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { afterEach, vi, describe, expect, it } from 'vitest'
import App from './App'

afterEach(() => vi.restoreAllMocks())

describe('DeployGuard dashboard', () => {
  it('renders live dashboard metrics', async () => {
    vi.spyOn(globalThis, 'fetch').mockImplementation(async (input) => {
      const url = String(input)
      if (url.includes('/api/pipelines?')) {
        return {
          ok: true,
          json: async () => ({ data: [{ id: 1, name: 'ci-main', status: 'failure' }] }),
        } as Response
      }
      if (url.includes('/api/notifications?')) {
        return {
          ok: true,
          json: async () => ({ items: [] }),
        } as Response
      }
      return {
        ok: true,
        json: async () => ({
          pipeline_health: { total: 4, failed: 1, successful: 3 },
          test_reliability: {
            total_executions: 12,
            failed_executions: 2,
            flaky_tests: [{ test_name: 'login', runs: 5, pass_rate: 0.6 }],
          },
          infrastructure_findings: 3,
          recent_pipelines: [{ id: 1, name: 'ci-main', status: 'failure' }],
        }),
      } as Response
    })

    render(<App />)
    await waitFor(() => expect(screen.getByText('ci-main')).toBeInTheDocument())
    expect(screen.getByText('4')).toBeInTheDocument()
    expect(screen.getByText('login')).toBeInTheDocument()
  })

  it('shows an API error without fake metrics', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue({ ok: false, status: 503 } as Response)
    render(<App />)
    expect(await screen.findByRole('alert')).toHaveTextContent('API returned 503')
  })
})
