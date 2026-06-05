import { useEffect, useState } from 'react'
import Editor from '@monaco-editor/react'
import {
  type Comment,
  type RunResult,
  type Session,
  WS_BASE_URL,
  createComment,
  createReply,
  createSession,
  getComments,
  getSession,
  runCode,
} from './api'
import './App.css'

const initialCode = `def solve():
    numbers = [3, 1, 4, 1, 5]
    total = sum(numbers)
    print("Total:", total)

solve()
`

type WsEventLog = {
  type: string
  message: string
  time: string
}

function App() {
  const [sessionTitle, setSessionTitle] = useState('Python Debug Session')
  const [joinSessionId, setJoinSessionId] = useState('')
  const [session, setSession] = useState<Session | null>(null)

  const [code, setCode] = useState(initialCode)
  const [stdin, setStdin] = useState('')
  const [runResult, setRunResult] = useState<RunResult | null>(null)

  const [comments, setComments] = useState<Comment[]>([])
  const [lineNumber, setLineNumber] = useState(1)
  const [commentBody, setCommentBody] = useState('')
  const [authorName, setAuthorName] = useState('')

  const [replyBodies, setReplyBodies] = useState<Record<string, string>>({})
  const [events, setEvents] = useState<WsEventLog[]>([])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!error) return

    const timer = window.setTimeout(() => {
      setError('')
    }, 3500)

    return () => window.clearTimeout(timer)
  }, [error])

  const refreshComments = async (sessionId: string) => {
    const data = await getComments(sessionId)
    setComments(data.comments)
  }

  const handleCreateSession = async () => {
    try {
      setError('')
      setLoading(true)
      const created = await createSession(sessionTitle)
      setSession(created)
      setJoinSessionId(created.session_id)
      await refreshComments(created.session_id)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create session')
    } finally {
      setLoading(false)
    }
  }

  const handleJoinSession = async () => {
    if (!joinSessionId.trim()) {
      setError('Please enter a session ID.')
      return
    }

    try {
      setError('')
      setLoading(true)
      const loaded = await getSession(joinSessionId.trim())
      setSession(loaded)
      await refreshComments(loaded.session_id)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to join session')
    } finally {
      setLoading(false)
    }
  }

  const handleRunCode = async () => {
    if (!session) {
      setError('Create or join a session first.')
      return
    }

    try {
      setError('')
      setLoading(true)
      const result = await runCode(session.session_id, code, stdin)
      setRunResult(result)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to run code')
    } finally {
      setLoading(false)
    }
  }

  const handleCreateComment = async () => {
    if (!session) {
      setError('Create or join a session first.')
      return
    }

    if (!commentBody.trim()) {
      setError('Please write a comment.')
      return
    }

    try {
      setError('')
      setLoading(true)
      await createComment(session.session_id, lineNumber, commentBody, authorName || 'Mentee')
      setCommentBody('')
      await refreshComments(session.session_id)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create comment')
    } finally {
      setLoading(false)
    }
  }

  const handleCreateReply = async (commentId: string) => {
    if (!session) return

    const body = replyBodies[commentId]
    if (!body?.trim()) return

    try {
      setError('')
      setLoading(true)
      await createReply(session.session_id, commentId, body, authorName || 'Mentor')
      setReplyBodies((prev) => ({ ...prev, [commentId]: '' }))
      await refreshComments(session.session_id)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create reply')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (!session) return

    const ws = new WebSocket(`${WS_BASE_URL}/ws/sessions/${session.session_id}`)

    ws.onopen = () => {
      setEvents((prev) => [
        {
          type: 'ws.connected',
          message: 'WebSocket connected.',
          time: new Date().toLocaleTimeString(),
        },
        ...prev,
      ].slice(0, 20))
    }

    ws.onmessage = async (event) => {
      try {
        const data = JSON.parse(event.data)

        if (data.type === 'pong') return

        setEvents((prev) => [
          {
            type: data.type ?? 'unknown',
            message: `Received event for session ${data.session_id ?? session.session_id}`,
            time: new Date().toLocaleTimeString(),
          },
          ...prev,
        ].slice(0, 20))

        if (
          data.type === 'comment.created' ||
          data.type === 'reply.created' ||
          data.type === 'session.run.completed'
        ) {
          await refreshComments(session.session_id)
        }
      } catch {
        setEvents((prev) => [
          {
            type: 'ws.message',
            message: String(event.data),
            time: new Date().toLocaleTimeString(),
          },
          ...prev,
        ].slice(0, 20))
      }
    }

    const heartbeat = window.setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send('ping')
      }
    }, 15000)

    ws.onerror = () => {
      setEvents((prev) => [
        {
          type: 'ws.error',
          message: 'WebSocket error occurred.',
          time: new Date().toLocaleTimeString(),
        },
        ...prev,
      ].slice(0, 20))
    }

    ws.onclose = () => {
      setEvents((prev) => [
        {
          type: 'ws.closed',
          message: 'WebSocket disconnected.',
          time: new Date().toLocaleTimeString(),
        },
        ...prev,
      ].slice(0, 20))
    }

    return () => {
      window.clearInterval(heartbeat)
      ws.close()
    }
  }, [session])

  return (
    <main className="app">
      <header className="topbar">
        <div>
          <p className="eyebrow">Cloudterm</p>
          <h1>Cloudterm Code Mentoring</h1>
          <p className="subtitle">
            Write Python code, run it safely inside a Docker sandbox, and discuss line-based questions with realtime backend updates.
          </p>
        </div>

        <div className="session-card">
          <span>Current Session</span>
          <strong>{session?.title ?? 'No session selected'}</strong>
          <small>{session?.session_id ?? 'Create or join a session first'}</small>
        </div>
      </header>

      {error && (
        <div className="toast-error">
          <span>{error}</span>
          <button type="button" className="toast-close" onClick={() => setError('')}>
            ×
          </button>
        </div>
      )}

      <section className="session-actions">
        <div className="card">
          <h2>Create Session</h2>
          <input
            value={sessionTitle}
            onChange={(event) => setSessionTitle(event.target.value)}
            placeholder="Session title"
          />
          <button type="button" onClick={handleCreateSession} disabled={loading}>
            Create Session
          </button>
        </div>

        <div className="card">
          <h2>Join Session</h2>
          <input
            value={joinSessionId}
            onChange={(event) => setJoinSessionId(event.target.value)}
            placeholder="Session ID"
          />
          <button type="button" onClick={handleJoinSession} disabled={loading}>
            Join Session
          </button>
        </div>
      </section>

      <section className="layout">
        <section className="editor-panel">
          <div className="panel-header">
            <div>
              <h2>Python Code</h2>
              <p>Code is sent to backend and executed by Runner/Docker sandbox.</p>
            </div>

            <div className="editor-actions">
              <button
                type="button"
                className="secondary-button"
                onClick={() =>
                  setCode(`print("Hello from Cloudterm!")
numbers = [1, 2, 3, 4]
print("Total:", sum(numbers))`)
                }
              >
                Success Demo
              </button>

              <button
                type="button"
                className="secondary-button"
                onClick={() =>
                  setCode(`numbers = [1, 2, 3]
            print(total)
            `)
                }
              >
                Error Demo
              </button>

              <button
                type="button"
                className="secondary-button"
                onClick={() =>
                  setCode(`while True:
                pass
            `)
                }
              >
                Timeout Demo
              </button>

              <button type="button" onClick={handleRunCode} disabled={loading || !session}>
                Run Code
              </button>
            </div>
          </div>

          <div className="editor-box">
            <Editor
              height="430px"
              defaultLanguage="python"
              theme="vs-dark"
              value={code}
              onChange={(value) => setCode(value ?? '')}
              options={{
                fontSize: 14,
                minimap: { enabled: false },
                wordWrap: 'on',
                automaticLayout: true,
              }}
            />
          </div>

          <label>stdin</label>
          <textarea
            className="stdin-box"
            value={stdin}
            onChange={(event) => setStdin(event.target.value)}
            placeholder="Optional input for the program"
          />
        </section>

        <aside className="side-panel">
          <section className="card">
            <h2>Execution Result</h2>

            <div className="result-grid">
              <div>
                <span>Exit Code</span>
                <strong>{runResult?.exit_code ?? '-'}</strong>
              </div>
              <div>
                <span>Timed Out</span>
                <strong>{runResult ? String(runResult.timed_out) : '-'}</strong>
              </div>
            </div>

            <label>stdout</label>
            <pre className="terminal success">{runResult?.stdout || '(empty)'}</pre>

            <label>stderr</label>
            <pre className="terminal error">{runResult?.stderr || '(empty)'}</pre>
          </section>

          <section className="card">
            <h2>WebSocket Events</h2>

            <div className="event-list">
              {events.length === 0 && <p className="empty">No events yet.</p>}
              {events.map((event, index) => (
                <div className="event" key={`${event.type}-${index}`}>
                  <strong>{event.type}</strong>
                  <p>{event.message}</p>
                  <small>{event.time}</small>
                </div>
              ))}
            </div>
          </section>
        </aside>
      </section>

      <section className="comments-panel">
        <div className="panel-header">
          <div>
            <h2>Line Questions & Replies</h2>
            <p>Comments are saved and loaded from backend API.</p>
          </div>
        </div>

        <div className="comment-form">
          <input
            type="number"
            min="1"
            value={lineNumber}
            onChange={(event) => setLineNumber(Number(event.target.value))}
            placeholder="Line"
          />
          <input
            value={authorName}
            onChange={(event) => setAuthorName(event.target.value)}
            placeholder="Your name or role"
          />
          <input
            value={commentBody}
            onChange={(event) => setCommentBody(event.target.value)}
            placeholder="Question for this line"
          />
          <button type="button" onClick={handleCreateComment} disabled={loading || !session}>
            Add Comment
          </button>
        </div>

        <div className="comments-grid">
          {comments.length === 0 && <p className="empty">No comments yet.</p>}

          {comments.map((comment) => (
            <article className="comment-card" key={comment.comment_id}>
              <div className="comment-line">Line {comment.line_number}</div>
              <h3>{comment.body}</h3>
              <p className="meta">
                Asked by {comment.author_name} · {comment.created_at}
              </p>

              {comment.replies.map((reply) => (
                <div className="reply" key={reply.reply_id}>
                  <strong>{reply.author_name}</strong>
                  <p>{reply.body}</p>
                  <small>{reply.created_at}</small>
                </div>
              ))}

              <div className="reply-form">
                <input
                  value={replyBodies[comment.comment_id] ?? ''}
                  onChange={(event) =>
                    setReplyBodies((prev) => ({
                      ...prev,
                      [comment.comment_id]: event.target.value,
                    }))
                  }
                  placeholder="Write reply"
                />
                <button
                  type="button"
                  onClick={() => handleCreateReply(comment.comment_id)}
                  disabled={loading || !session}
                >
                  Reply
                </button>
              </div>
            </article>
          ))}
        </div>
      </section>
    </main>
  )
}

export default App