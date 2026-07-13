import { useState, useRef, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { api } from '../api/client'

const SUGGESTIONS = [
  'What does this repo do?',
  'How is the codebase structured?',
  'What are the main dependencies?',
  'How do I set up the project locally?',
  'What design patterns are used?',
]

export default function ChatInterface({ repoUrl }) {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: "I've indexed this repository. Ask me anything about the code — architecture, logic, how to use it, or anything else.",
    },
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const bottomRef = useRef(null)
  const textareaRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  async function send(question) {
    const q = question || input.trim()
    if (!q || isLoading) return

    setMessages((prev) => [...prev, { role: 'user', content: q }])
    setInput('')
    setIsLoading(true)

    try {
      const data = await api.qa(repoUrl, q)
      setMessages((prev) => [...prev, { role: 'assistant', content: data.answer }])
    } catch (e) {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: `Error: ${e.message}` },
      ])
    } finally {
      setIsLoading(false)
    }
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      send()
    }
  }

  const showSuggestions = messages.length === 1 && !isLoading

  return (
    <div className="chat-wrapper">
      <div className="chat-messages">
        {messages.map((msg, i) => (
          <div key={i} className={`message message-${msg.role}`}>
            <div className="message-bubble">
              {msg.role === 'assistant' ? (
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {msg.content}
                </ReactMarkdown>
              ) : (
                <p>{msg.content}</p>
              )}
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="message message-assistant">
            <div className="message-bubble">
              <div className="typing-indicator">
                <span /><span /><span />
              </div>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {showSuggestions && (
        <div className="suggestions">
          {SUGGESTIONS.map((s) => (
            <button key={s} className="suggestion-chip" onClick={() => send(s)}>
              {s}
            </button>
          ))}
        </div>
      )}

      <div className="chat-input-row">
        <textarea
          ref={textareaRef}
          className="chat-input"
          rows={1}
          placeholder="Ask a question about the codebase…"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isLoading}
        />
        <button
          className="chat-send-btn"
          onClick={() => send()}
          disabled={isLoading || !input.trim()}
        >
          {isLoading ? <span className="spinner" /> : '↑'}
        </button>
      </div>
    </div>
  )
}
