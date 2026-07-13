import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { api } from '../api/client'

export default function ArchitectureTab({ repoUrl }) {
  const [content, setContent] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const [copied, setCopied] = useState(false)

  async function generate() {
    setIsLoading(true)
    setError('')
    try {
      const data = await api.architecture(repoUrl)
      setContent(data.architecture)
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
          <h2 className="generate-title">Architecture Summary</h2>
          <p className="generate-desc">
            Get a full architectural overview: tech stack, component relationships, data flow, and design patterns.
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
              <><span className="spinner" style={{ width: 14, height: 14 }} /> Analyzing…</>
            ) : (
              content ? 'Re-analyze' : 'Analyze Architecture'
            )}
          </button>
        </div>
      </div>

      {error && <div className="error-banner">{error}</div>}

      {!content && !isLoading && (
        <div className="generate-empty">
          <span className="generate-empty-icon">🏗️</span>
          <p>Click <strong>Analyze Architecture</strong> to generate an architectural overview.</p>
        </div>
      )}

      {isLoading && (
        <div className="generate-loading">
          <span className="spinner" />
          <p>Analyzing codebase architecture…</p>
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
