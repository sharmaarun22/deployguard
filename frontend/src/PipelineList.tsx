import { useEffect, useState } from 'react'

type Pipeline = {
  id: number
  name: string
  status: string
}

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function PipelineList() {
  const [pipelines, setPipelines] = useState<Pipeline[]>([])

  useEffect(() => {
    fetch(`${API_URL}/api/pipelines?limit=25&offset=0`)
      .then((response) => response.json())
      .then((value: { data: Pipeline[] }) => setPipelines(value.data))
  }, [])

  return (
    <article className="panel">
      <h2>Pipelines</h2>
      {pipelines.map((pipeline) => (
        <div className="row" key={pipeline.id}>
          <span>{pipeline.name}</span>
          <b className={`badge ${pipeline.status}`}>{pipeline.status}</b>
        </div>
      ))}
    </article>
  )
}

export default PipelineList
