import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { api } from '../api/client'

export default function ReadmeTab({ repoUrl }) {
  const [content, setContent] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const [copied, setCopied] = useState(false)

  async function generate() {
    setIsLoading(true)
    setError('')
    try {
      const data = await api.readme(repoUrl)
      setContent(data.readme)
    } catch (e) {
      setError(e.message)
    } finally {
      setIsLoading(false)
    }
  }

  async function copyToClipboard() {
    await navigator.clipboard.writeText(content)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="generate-tab">
      <div className="generate-header">
        <div>
          <h2 className="generate-title">README Generator</h2>
          <p className="generate-desc">
            Generate a comprehensive README with setup instructions, usage examples, and API documentation.
          </p>
        </div>
        <div className="generate-actions">
          {content && (
            <button className="btn-secondary" onClick={copyToClipboard}>
              {copied ? '✓ Copied!' : 'Copy Markdown'}
            </button>
          )}
          <button className="btn-primary" onClick={generate} disabled={isLoading}>
            {isLoading ? (
              <><span className="spinner" style={{ width: 14, height: 14 }} /> Generating…</>
            ) : (
              content ? 'Regenerate' : 'Generate README'
            )}
          </button>
        </div>
      </div>

      {error && <div className="error-banner">{error}</div>}

      {!content && !isLoading && (
        <div className="generate-empty">
          <span className="generate-empty-icon">📄</span>
          <p>Click <strong>Generate README</strong> to create documentation for this repository.</p>
        </div>
      )}

      {isLoading && (
        <div className="generate-loading">
          <span className="spinner" />
          <p>Analyzing repository and generating README…</p>
        </div>
      )}

      {content && !isLoading && (
        <div className="markdown-output">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
        </div>
      )}

      {copied && <div className="copy-toast">Copied to clipboard!</div>}
    </div>
  )
}
