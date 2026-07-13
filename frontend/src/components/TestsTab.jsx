import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { api } from '../api/client'

export default function TestsTab({ repoUrl }) {
  const [targetFile, setTargetFile] = useState('')
  const [content, setContent] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const [copied, setCopied] = useState(false)

  async function generate() {
    setIsLoading(true)
    setError('')
    try {
      const data = await api.tests(repoUrl, targetFile)
      setContent(data.tests)
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
          <h2 className="generate-title">Unit Test Generator</h2>
          <p className="generate-desc">
            Generate test suites using the repository's existing test framework and patterns.
          </p>
        </div>
        <div className="generate-actions">
          {content && (
            <button className="btn-secondary" onClick={copyToClipboard}>
              {copied ? '✓ Copied!' : 'Copy Tests'}
            </button>
          )}
          <button className="btn-primary" onClick={generate} disabled={isLoading}>
            {isLoading ? (
              <><span className="spinner" style={{ width: 14, height: 14 }} /> Generating…</>
            ) : (
              content ? 'Regenerate' : 'Generate Tests'
            )}
          </button>
        </div>
      </div>

      <div className="target-file-row">
        <label className="target-file-label" htmlFor="target-file">
          Target file <span className="target-file-optional">(optional)</span>
        </label>
        <input
          id="target-file"
          className="target-file-input"
          type="text"
          placeholder="e.g. src/utils/parser.py — leave blank to test the whole repo"
          value={targetFile}
          onChange={(e) => setTargetFile(e.target.value)}
          disabled={isLoading}
        />
      </div>

      {error && <div className="error-banner">{error}</div>}

      {!content && !isLoading && (
        <div className="generate-empty">
          <span className="generate-empty-icon">🧪</span>
          <p>
            Optionally specify a target file, then click <strong>Generate Tests</strong>.
          </p>
        </div>
      )}

      {isLoading && (
        <div className="generate-loading">
          <span className="spinner" />
          <p>Detecting test framework and generating tests…</p>
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
