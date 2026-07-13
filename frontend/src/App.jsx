import { useState } from 'react'
import { api } from './api/client'
import RepoInput from './components/RepoInput'
import ChatInterface from './components/ChatInterface'
import ReadmeTab from './components/ReadmeTab'
import TestsTab from './components/TestsTab'
import ArchitectureTab from './components/ArchitectureTab'

const TABS = [
  { id: 'chat', label: 'Q&A Chat', icon: '💬' },
  { id: 'readme', label: 'README', icon: '📄' },
  { id: 'tests', label: 'Unit Tests', icon: '🧪' },
  { id: 'architecture', label: 'Architecture', icon: '🏗️' },
]

export default function App() {
  const [repoUrl, setRepoUrl] = useState('')
  const [isIngesting, setIsIngesting] = useState(false)
  const [isIngested, setIsIngested] = useState(false)
  const [repoInfo, setRepoInfo] = useState(null)
  const [activeTab, setActiveTab] = useState('chat')
  const [error, setError] = useState('')

  async function handleIngest(url) {
    setIsIngesting(true)
    setError('')
    try {
      const data = await api.ingest(url)
      setRepoUrl(url)
      setRepoInfo(data)
      setIsIngested(true)
      setActiveTab('chat')
    } catch (e) {
      setError(e.message)
    } finally {
      setIsIngesting(false)
    }
  }

  function handleReset() {
    setIsIngested(false)
    setRepoUrl('')
    setRepoInfo(null)
    setError('')
    setActiveTab('chat')
  }

  return (
    <div className="app">
      <header className="header">
        <div className="header-inner">
          <div className="logo">
            <span className="logo-icon">⚡</span>
            <span className="logo-text">Repo Copilot</span>
          </div>
          {isIngested && repoInfo && (
            <div className="repo-badge">
              <span className="repo-badge-dot" />
              <span className="repo-badge-name">{repoInfo.full_name || repoUrl}</span>
              <button className="repo-badge-reset" onClick={handleReset} title="Load different repo">
                ✕
              </button>
            </div>
          )}
        </div>
      </header>

      <main className="main">
        {!isIngested ? (
          <div className="hero">
            <h1 className="hero-title">
              Understand any GitHub repo<br />
              <span className="hero-accent">in seconds</span>
            </h1>
            <p className="hero-subtitle">
              Paste a GitHub repository URL to index it with AI. Then ask questions,
              generate documentation, write tests, and explore the architecture.
            </p>

            <RepoInput
              onIngest={handleIngest}
              isIngesting={isIngesting}
              error={error}
            />

            <div className="feature-grid">
              <div className="feature-card">
                <span className="feature-icon">💬</span>
                <h3>Q&amp;A Chat</h3>
                <p>Ask anything about the codebase — architecture, logic, dependencies, patterns.</p>
              </div>
              <div className="feature-card">
                <span className="feature-icon">📄</span>
                <h3>README Generator</h3>
                <p>Auto-generate a comprehensive README with setup, usage, and API docs.</p>
              </div>
              <div className="feature-card">
                <span className="feature-icon">🧪</span>
                <h3>Unit Tests</h3>
                <p>Generate test suites for any file using the repo's existing test framework.</p>
              </div>
              <div className="feature-card">
                <span className="feature-icon">🏗️</span>
                <h3>Architecture</h3>
                <p>Get a full architecture summary: tech stack, data flow, design patterns.</p>
              </div>
            </div>
          </div>
        ) : (
          <div className="workspace">
            <nav className="tabs">
              {TABS.map((tab) => (
                <button
                  key={tab.id}
                  className={`tab-btn${activeTab === tab.id ? ' active' : ''}`}
                  onClick={() => setActiveTab(tab.id)}
                >
                  <span>{tab.icon}</span>
                  <span>{tab.label}</span>
                </button>
              ))}
            </nav>

            <div className="tab-content">
              <div className={activeTab === 'chat' ? 'tab-panel active' : 'tab-panel'}>
                <ChatInterface repoUrl={repoUrl} />
              </div>
              <div className={activeTab === 'readme' ? 'tab-panel active' : 'tab-panel'}>
                <ReadmeTab repoUrl={repoUrl} />
              </div>
              <div className={activeTab === 'tests' ? 'tab-panel active' : 'tab-panel'}>
                <TestsTab repoUrl={repoUrl} />
              </div>
              <div className={activeTab === 'architecture' ? 'tab-panel active' : 'tab-panel'}>
                <ArchitectureTab repoUrl={repoUrl} />
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}
