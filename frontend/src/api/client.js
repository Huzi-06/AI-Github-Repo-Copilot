const BASE = import.meta.env.VITE_API_URL || '/api'

async function request(endpoint, body) {
  const res = await fetch(`${BASE}${endpoint}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  const data = await res.json()
  if (!res.ok) {
    throw new Error(data.detail || `Request failed with status ${res.status}`)
  }
  return data
}

export const api = {
  ingest:       (repoUrl)              => request('/ingest',       { repo_url: repoUrl }),
  qa:           (repoUrl, question)    => request('/qa',           { repo_url: repoUrl, question }),
  readme:       (repoUrl)              => request('/readme',       { repo_url: repoUrl }),
  tests:        (repoUrl, targetFile)  => request('/tests',        { repo_url: repoUrl, target_file: targetFile || null }),
  architecture: (repoUrl)              => request('/architecture', { repo_url: repoUrl }),
}
