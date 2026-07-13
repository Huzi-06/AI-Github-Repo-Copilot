import { useState } from 'react'

const STEPS = [
  'Cloning repository metadata…',
  'Fetching file tree and contents…',
  'Chunking and embedding documents…',
  'Building vector index…',
  'Ready!',
]

export default function RepoInput({ onIngest, isIngesting, error }) {
  const [url, setUrl] = useState('')
  const [step, setStep] = useState(0)

  // Cycle through steps while ingesting
  if (isIngesting && step < STEPS.length - 1) {
    setTimeout(() => setStep((s) => Math.min(s + 1, STEPS.length - 2)), 1800)
  }
  if (!isIngesting && step !== 0) {
    setStep(0)
  }

  function handleSubmit(e) {
    e.preventDefault()
    const trimmed = url.trim()
    if (!trimmed) return
    onIngest(trimmed)
  }

  return (
    <div className="repo-input-wrapper">
      <form className="repo-input-form" onSubmit={handleSubmit}>
        <div className="repo-input-row">
          <span className="repo-input-prefix">github.com/</span>
          <input
            className="repo-input"
            type="text"
            placeholder="owner/repo  or  https://github.com/owner/repo"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            disabled={isIngesting}
            spellCheck={false}
            autoComplete="off"
          />
          <button
            className="repo-input-btn"
            type="submit"
            disabled={isIngesting || !url.trim()}
          >
            {isIngesting ? (
              <span className="spinner" />
            ) : (
              'Analyze →'
            )}
          </button>
        </div>
      </form>

      {isIngesting && (
        <div className="ingesting-banner">
          <span className="spinner" style={{ width: 14, height: 14 }} />
          <span>{STEPS[step]}</span>
        </div>
      )}

      {error && !isIngesting && (
        <div className="error-banner">{error}</div>
      )}
    </div>
  )
}
