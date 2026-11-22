import { useEffect, useState } from 'react'
import './App.css'

type Dashboard = {
  pipeline_health: { total: number; failed: number; successful: number }
  test_reliability: {
    total_executions: number
    failed_executions: number
    flaky_tests: Array<{ test_name: string; runs: number; pass_rate: number }>
  }
  infrastructure_findings: number
  recent_pipelines: Array<{ id: number; name: string; status: string }>
}

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function App() {
  const [dashboard, setDashboard] = useState<Dashboard | null>(null)
  const [error, setError] = useState('')
  const [connected, setConnected] = useState(false)

  useEffect(() => {
    fetch(`${API_URL}/api/dashboard`)
      .then((response) => {
        if (!response.ok) throw new Error(`API returned ${response.status}`)
        return response.json()
      })
      .then((value: Dashboard) => {
        setDashboard(value)
        setConnected(true)
      })
      .catch((reason: unknown) => {
        setError(reason instanceof Error ? reason.message : 'Unable to reach DeployGuard')
        setConnected(false)
      })
  }, [])

  return (
    <main>
      <header className="topbar">
        <div>
          <p className="eyebrow">DEPLOYGUARD</p>
          <h1>CI/CD Intelligence</h1>
        </div>
        <span className="status"><i className={connected ? '' : 'offline'} /> {connected ? 'API connected' : 'API unavailable'}</span>
      </header>

      {error && <div className="alert" role="alert">{error}</div>}
      {!dashboard && !error && <p className="loading">Loading dashboard...</p>}

      {dashboard && (
        <>
          <section className="metrics" aria-label="Pipeline health">
            <article>
              <span>PIPELINES</span>
              <strong>{dashboard.pipeline_health.total}</strong>
              <small>{dashboard.pipeline_health.successful} successful</small>
            </article>
            <article>
              <span>FAILED PIPELINES</span>
              <strong>{dashboard.pipeline_health.failed}</strong>
              <small>requires investigation</small>
            </article>
            <article>
              <span>TEST EXECUTIONS</span>
              <strong>{dashboard.test_reliability.total_executions}</strong>
              <small>{dashboard.test_reliability.failed_executions} failures</small>
            </article>
            <article>
              <span>INFRASTRUCTURE</span>
              <strong>{dashboard.infrastructure_findings}</strong>
              <small>static findings</small>
            </article>
          </section>

          <section className="content-grid">
            <article className="panel">
              <h2>Recent pipelines</h2>
              {dashboard.recent_pipelines.length === 0 ? (
                <p className="empty">No pipelines analyzed yet.</p>
              ) : (
                <div className="table">
                  {dashboard.recent_pipelines.map((pipeline) => (
                    <div className="row" key={pipeline.id}>
                      <span>{pipeline.name}</span>
                      <b className={`badge ${pipeline.status}`}>{pipeline.status}</b>
                    </div>
                  ))}
                </div>
              )}
            </article>

            <article className="panel">
              <h2>Flaky tests</h2>
              {dashboard.test_reliability.flaky_tests.length === 0 ? (
                <p className="empty">No flaky tests detected.</p>
              ) : (
                dashboard.test_reliability.flaky_tests.map((test) => (
                  <div className="row" key={test.test_name}>
                    <span>{test.test_name}</span>
                    <b>{Math.round(test.pass_rate * 100)}% pass</b>
                  </div>
                ))
              )}
            </article>
          </section>
        </>
      )}
    </main>
  )
}

export default App
