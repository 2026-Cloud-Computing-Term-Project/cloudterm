import { useEffect, useState } from 'react'
import Editor from '@monaco-editor/react'
import {
  type Comment,
  type RunHistoryItem,
  type RunResult,
  type Session,
  WS_BASE_URL,
  createComment,
  createReply,
  createSession,
  getComments,
  getRuns,
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

type Toast = {
  type: 'error' | 'success' | 'info'
  message: string
}

function App() {
  const [sessionTitle, setSessionTitle] = useState('Python Debug Session')
  const [joinSessionId, setJoinSessionId] = useState('')
  const [session, setSession] = useState<Session | null>(null)

  const [code, setCode] = useState(initialCode)
  const [stdin, setStdin] = useState('')
  const [runResult, setRunResult] = useState<RunResult | null>(null)
  const [runHistory, setRunHistory] = useState<RunHistoryItem[]>([])
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null)

  const [comments, setComments] = useState<Comment[]>([])
  const [lineNumber, setLineNumber] = useState(1)
  const [commentBody, setCommentBody] = useState('')
  const [authorName, setAuthorName] = useState('')

  const [replyBodies, setReplyBodies] = useState<Record<string, string>>({})
  const [events, setEvents] = useState<WsEventLog[]>([])
  const [toast, setToast] = useState<Toast | null>(null)
  const [loading, setLoading] = useState(false)

  const isBackendReady = Boolean(session)
  const isWebSocketLive = events.some((event) => event.type === 'ws.connected')
  const selectedRun =
    selectedRunId ? runHistory.find((run) => run.run_id === selectedRunId) ?? null : null
  const displayedRun = selectedRun ?? runResult
  const isRunnerTested = Boolean(displayedRun) || runHistory.length > 0

  const showToast = (type: Toast['type'], message: string) => {
    setToast({ type, message })
  }

  useEffect(() => {
    if (!toast) return

    const timer = window.setTimeout(() => {
      setToast(null)
    }, 3500)

    return () => window.clearTimeout(timer)
  }, [toast])

  const addEvent = (event: WsEventLog) => {
    setEvents((prev) => [event, ...prev].slice(0, 20))
  }

  const getShareLink = (sessionId: string) => {
    return `${window.location.origin}/sessions/${sessionId}`
  }

  const moveToSessionUrl = (sessionId: string) => {
    window.history.pushState(null, '', `/sessions/${sessionId}`)
  }

  const moveToHomeUrl = () => {
    window.history.pushState(null, '', '/')
  }

  const refreshComments = async (sessionId: string) => {
    const data = await getComments(sessionId)
    setComments(data.comments)
  }

  const refreshRuns = async (sessionId: string) => {
    const data = await getRuns(sessionId)
    setRunHistory(data.runs)
    setSelectedRunId((currentRunId) => {
      if (data.runs.length === 0) return null
      if (currentRunId && data.runs.some((run) => run.run_id === currentRunId)) {
        return currentRunId
      }
      return data.runs[0].run_id
    })
    return data.runs
  }

  const restoreRunSnapshot = (run: RunHistoryItem) => {
    setSelectedRunId(run.run_id)
    setCode(run.code)
    setStdin(run.stdin)
  }

  const loadSession = async (sessionId: string) => {
    const loaded = await getSession(sessionId)
    setSession(loaded)
    setJoinSessionId(loaded.session_id)
    const [, runs] = await Promise.all([
      refreshComments(loaded.session_id),
      refreshRuns(loaded.session_id),
    ])
    if (runs[0]) {
      restoreRunSnapshot(runs[0])
    }
  }

  useEffect(() => {
    const pathSessionId = window.location.pathname.split('/sessions/')[1]

    if (!pathSessionId) return

    const cleanSessionId = pathSessionId.split('/')[0]

    if (!cleanSessionId) return

    const timer = window.setTimeout(() => {
      setLoading(true)

      getSession(cleanSessionId)
        .then(async (loaded) => {
          setSession(loaded)
          setJoinSessionId(loaded.session_id)

          const [, runs] = await Promise.all([
            refreshComments(loaded.session_id),
            refreshRuns(loaded.session_id),
          ])
          if (runs[0]) {
            restoreRunSnapshot(runs[0])
          }

          setToast({
            type: 'success',
            message: 'Joined session from link.',
          })
        })
        .catch((err) =>
          setToast({
            type: 'error',
            message:
              err instanceof Error ? err.message : 'Failed to join session from link.',
          }),
        )
        .finally(() => setLoading(false))
    }, 0)

    return () => window.clearTimeout(timer)
  }, [])

  const handleCreateSession = async () => {
    try {
      setLoading(true)
      const created = await createSession(sessionTitle)
      setSession(created)
      setJoinSessionId(created.session_id)
      moveToSessionUrl(created.session_id)
      await Promise.all([refreshComments(created.session_id), refreshRuns(created.session_id)])
      showToast('success', 'Session created successfully.')
    } catch (err) {
      showToast('error', err instanceof Error ? err.message : 'Failed to create session')
    } finally {
      setLoading(false)
    }
  }

  const handleJoinSession = async () => {
    if (!joinSessionId.trim()) {
      showToast('error', 'Please enter a session ID.')
      return
    }

    try {
      setLoading(true)
      const sessionId = joinSessionId.trim()
      await loadSession(sessionId)
      moveToSessionUrl(sessionId)
      showToast('success', 'Joined session successfully.')
    } catch (err) {
      showToast('error', err instanceof Error ? err.message : 'Failed to join session')
    } finally {
      setLoading(false)
    }
  }

  const handleBackToHub = () => {
    setSession(null)
    setRunResult(null)
    setRunHistory([])
    setSelectedRunId(null)
    setComments([])
    setEvents([])
    moveToHomeUrl()
  }

  const handleCopyLink = async () => {
    if (!session) return

    const link = getShareLink(session.session_id)

    try {
      await navigator.clipboard.writeText(link)
      showToast('success', 'Session link copied.')
    } catch {
      showToast('error', 'Failed to copy session link.')
    }
  }

  const handleRunCode = async () => {
    if (!session) {
      showToast('error', 'Create or join a session first.')
      return
    }

    try {
      setLoading(true)
      const result = await runCode(session.session_id, code, stdin)
      setRunResult(result)
      await refreshRuns(session.session_id)
      setSelectedRunId(result.run_id)

      if (result.timed_out) {
        showToast('info', 'Code execution timed out inside the sandbox.')
      } else if (result.exit_code === 0) {
        showToast('success', 'Code executed successfully.')
      } else {
        showToast('error', 'Code finished with an error.')
      }
    } catch (err) {
      showToast('error', err instanceof Error ? err.message : 'Failed to run code')
    } finally {
      setLoading(false)
    }
  }

  const handleCreateComment = async () => {
    if (!session) {
      showToast('error', 'Create or join a session first.')
      return
    }

    if (!commentBody.trim()) {
      showToast('error', 'Please write a comment.')
      return
    }

    try {
      setLoading(true)
      await createComment(session.session_id, lineNumber, commentBody, authorName || 'Mentee')
      setCommentBody('')
      await refreshComments(session.session_id)
      showToast('success', 'Comment added.')
    } catch (err) {
      showToast('error', err instanceof Error ? err.message : 'Failed to create comment')
    } finally {
      setLoading(false)
    }
  }

  const handleCreateReply = async (commentId: string) => {
    if (!session) return

    const body = replyBodies[commentId]
    if (!body?.trim()) {
      showToast('error', 'Please write a reply.')
      return
    }

    try {
      setLoading(true)
      await createReply(session.session_id, commentId, body, authorName || 'Mentor')
      setReplyBodies((prev) => ({ ...prev, [commentId]: '' }))
      await refreshComments(session.session_id)
      showToast('success', 'Reply added.')
    } catch (err) {
      showToast('error', err instanceof Error ? err.message : 'Failed to create reply')
    } finally {
      setLoading(false)
    }
  }

  const handleSelectRun = (run: RunHistoryItem) => {
    restoreRunSnapshot(run)
  }

  const formatRunTime = (value: string) => {
    return new Date(value).toLocaleString()
  }

  useEffect(() => {
    if (!session) return

    const ws = new WebSocket(`${WS_BASE_URL}/ws/sessions/${session.session_id}`)

    ws.onopen = () => {
      addEvent({
        type: 'ws.connected',
        message: 'WebSocket connected.',
        time: new Date().toLocaleTimeString(),
      })
      showToast('success', 'Realtime connection is live.')
    }

    ws.onmessage = async (event) => {
      if (event.data === 'pong') return

      try {
        const data = JSON.parse(event.data)

        if (data.type === 'pong') return

        addEvent({
          type: data.type ?? 'unknown',
          message: `Received event for session ${data.session_id ?? session.session_id}`,
          time: new Date().toLocaleTimeString(),
        })

        if (data.type === 'comment.created') {
          showToast('info', 'New comment received.')
          await refreshComments(session.session_id)
        }

        if (data.type === 'reply.created') {
          showToast('info', 'New reply received.')
          await refreshComments(session.session_id)
        }

        if (data.type === 'session.run.completed') {
          showToast('info', 'Run completed event received.')
          await Promise.all([refreshComments(session.session_id), refreshRuns(session.session_id)])
        }
      } catch {
        addEvent({
          type: 'ws.message',
          message: String(event.data),
          time: new Date().toLocaleTimeString(),
        })
      }
    }

    const heartbeat = window.setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send('ping')
      }
    }, 15000)

    ws.onerror = () => {
      addEvent({
        type: 'ws.error',
        message: 'WebSocket error occurred.',
        time: new Date().toLocaleTimeString(),
      })
      showToast('error', 'WebSocket error occurred.')
    }

    ws.onclose = () => {
      addEvent({
        type: 'ws.closed',
        message: 'WebSocket disconnected.',
        time: new Date().toLocaleTimeString(),
      })
    }

    return () => {
      window.clearInterval(heartbeat)
      ws.close()
    }
  }, [session])

  if (!session) {
    return (
      <main className="app">
        {toast && (
          <div className={`toast toast-${toast.type}`}>
            <span>{toast.message}</span>
            <button type="button" className="toast-close" onClick={() => setToast(null)}>
              ×
            </button>
          </div>
        )}

        <section className="hub">
          <div className="hub-hero">
            <p className="eyebrow">CodeSession</p>
            <h1>CodeSession Code Mentoring</h1>
            <p className="subtitle">
              Create a coding session, run Python code inside a Docker sandbox,
              and discuss line-based questions in realtime.
            </p>

            <div className="status-row">
              <span className="status-pill active">● Frontend Ready</span>
              <span className="status-pill">○ Waiting for Session</span>
              <span className="status-pill">○ Runner Not Tested</span>
            </div>
          </div>

          <div className="hub-grid">
            <div className="hub-card">
              <h2>Create New Session</h2>
              <p>Start a new code mentoring room and share the session link.</p>
              <input
                value={sessionTitle}
                onChange={(event) => setSessionTitle(event.target.value)}
                placeholder="Session title"
              />
              <button type="button" onClick={handleCreateSession} disabled={loading}>
                Create Session
              </button>
            </div>

            <div className="hub-card">
              <h2>Join Existing Session</h2>
              <p>Paste a session ID or open a shared session link.</p>
              <input
                value={joinSessionId}
                onChange={(event) => setJoinSessionId(event.target.value)}
                placeholder="Session ID"
              />
              <button type="button" onClick={handleJoinSession} disabled={loading}>
                Join Session
              </button>
            </div>
          </div>

          <section className="flow-strip hub-flow">
            <div>
              <strong>Frontend</strong>
              <span>React + Monaco</span>
            </div>
            <div className="flow-arrow">→</div>
            <div>
              <strong>Backend API</strong>
              <span>FastAPI</span>
            </div>
            <div className="flow-arrow">→</div>
            <div>
              <strong>Runner</strong>
              <span>Docker Sandbox</span>
            </div>
            <div className="flow-arrow">→</div>
            <div>
              <strong>Result</strong>
              <span>stdout / stderr</span>
            </div>
          </section>
        </section>
      </main>
    )
  }

  return (
    <main className="app">
      {toast && (
        <div className={`toast toast-${toast.type}`}>
          <span>{toast.message}</span>
          <button type="button" className="toast-close" onClick={() => setToast(null)}>
            ×
          </button>
        </div>
      )}

      <header className="topbar">
        <div>
          <p className="eyebrow">CodeSession Workspace</p>
          <h1>{session.title}</h1>
          <p className="subtitle">
            Write Python code, run it safely inside a Docker sandbox, and discuss
            line-based questions with realtime backend updates.
          </p>

          <div className="status-row">
            <span className={`status-pill ${isBackendReady ? 'active' : ''}`}>
              {isBackendReady ? '● Backend Connected' : '○ Backend Waiting'}
            </span>
            <span className={`status-pill ${isWebSocketLive ? 'active' : ''}`}>
              {isWebSocketLive ? '● WebSocket Live' : '○ WebSocket Idle'}
            </span>
            <span className={`status-pill ${isRunnerTested ? 'active' : ''}`}>
              {isRunnerTested ? '● Docker Runner Tested' : '○ Runner Not Tested'}
            </span>
          </div>
        </div>

        <div className="session-card">
          <span>Session Link</span>
          <strong>{session.session_id}</strong>
          <small>{getShareLink(session.session_id)}</small>
          <div className="session-card-actions">
            <button type="button" className="secondary-button" onClick={handleCopyLink}>
              Copy Link
            </button>
            <button type="button" className="secondary-button" onClick={handleBackToHub}>
              Back to Hub
            </button>
          </div>
        </div>
      </header>

      <section className="flow-strip">
        <div>
          <strong>Frontend</strong>
          <span>React + Monaco</span>
        </div>
        <div className="flow-arrow">→</div>
        <div>
          <strong>Backend API</strong>
          <span>FastAPI</span>
        </div>
        <div className="flow-arrow">→</div>
        <div>
          <strong>Runner</strong>
          <span>Docker Sandbox</span>
        </div>
        <div className="flow-arrow">→</div>
        <div>
          <strong>Result</strong>
          <span>stdout / stderr</span>
        </div>
      </section>

      <section className="layout">
        <section className="editor-panel">
          <div className="panel-header">
            <div>
              <h2>Code Editor</h2>
              <p>Code is sent to backend and executed by Runner/Docker sandbox.</p>
            </div>

            <div className="editor-actions">
              <button
                type="button"
                className="secondary-button"
                onClick={() =>
                  setCode(`print("Hello from CodeSession!")
numbers = [1, 2, 3, 4]
print("Total:", sum(numbers))
`)
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
                className="secondary-button danger-soft"
                onClick={() =>
                  setCode(`while True:
    pass
`)
                }
              >
                Timeout Demo
              </button>

              <button type="button" onClick={handleRunCode} disabled={loading}>
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
            <h2>Run Output</h2>

            <div className="result-grid">
              <div>
                <span>Exit Code</span>
                <strong>{displayedRun?.exit_code ?? '-'}</strong>
              </div>
              <div>
                <span>Timed Out</span>
                <strong>{displayedRun ? String(displayedRun.timed_out) : '-'}</strong>
              </div>
            </div>

            <label>stdout</label>
            <pre className="terminal success">{displayedRun?.stdout || '(empty)'}</pre>

            <label>stderr</label>
            <pre className="terminal error">{displayedRun?.stderr || '(empty)'}</pre>
          </section>

          <section className="card">
            <h2>Run History</h2>
            <p className="card-copy">Select a run to restore its code snapshot and output.</p>

            <div className="run-history-list">
              {runHistory.length === 0 && <p className="empty">No saved runs yet.</p>}
              {runHistory.map((run, index) => (
                <button
                  type="button"
                  className={`run-history-item ${run.run_id === selectedRunId ? 'active' : ''}`}
                  key={run.run_id}
                  onClick={() => handleSelectRun(run)}
                >
                  <span>Run {runHistory.length - index}</span>
                  <strong>
                    Exit {run.exit_code}
                    {run.timed_out ? ' · Timeout' : ''}
                  </strong>
                  <small>{formatRunTime(run.created_at)}</small>
                </button>
              ))}
            </div>
          </section>

          <section className="card">
            <h2>Realtime Events</h2>

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
            <h2>Mentor Comments</h2>
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
          <button type="button" onClick={handleCreateComment} disabled={loading}>
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
                  disabled={loading}
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
