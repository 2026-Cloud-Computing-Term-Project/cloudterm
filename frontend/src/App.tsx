import { useState } from 'react'
import Editor from '@monaco-editor/react'
import './App.css'

type RunResult = {
  run_id: string
  stdout: string
  stderr: string
  exit_code: number
  timed_out: boolean
}

type Reply = {
  reply_id: string
  body: string
  author_name: string
  created_at: string
}

type Comment = {
  comment_id: string
  line_number: number
  body: string
  author_name: string
  created_at: string
  replies: Reply[]
}

type WsEvent = {
  type: string
  message: string
  time: string
}

const initialCode = `def solve():
    numbers = [3, 1, 4, 1, 5]
    total = sum(numbers)
    print("Total:", total)

solve()
`

const mockComments: Comment[] = [
  {
    comment_id: 'comment-001',
    line_number: 2,
    body: 'Why do we store the numbers in a list first?',
    author_name: 'mentee',
    created_at: '2026-05-22T00:00:00Z',
    replies: [
      {
        reply_id: 'reply-001',
        body: 'Because it makes the input easier to reuse and test.',
        author_name: 'mentor',
        created_at: '2026-05-22T00:01:00Z',
      },
    ],
  },
  {
    comment_id: 'comment-002',
    line_number: 3,
    body: 'Can this line cause an error?',
    author_name: 'mentee',
    created_at: '2026-05-22T00:02:00Z',
    replies: [
      {
        reply_id: 'reply-002',
        body: 'It is safe here because every value in the list is a number.',
        author_name: 'mentor',
        created_at: '2026-05-22T00:03:00Z',
      },
    ],
  },
]

function App() {
  const [code, setCode] = useState(initialCode)
  const [runResult, setRunResult] = useState<RunResult>({
    run_id: 'run-mock-001',
    stdout: 'Total: 14\n',
    stderr: '',
    exit_code: 0,
    timed_out: false,
  })

  const [events, setEvents] = useState<WsEvent[]>([
    {
      type: 'comment.created',
      message: 'A line comment was created on line 2.',
      time: '00:00',
    },
    {
      type: 'reply.created',
      message: 'A mentor replied to a line comment.',
      time: '00:01',
    },
  ])

  const handleRunCode = () => {
    const nextResult: RunResult = {
      run_id: `run-mock-${Date.now()}`,
      stdout: 'Total: 14\n',
      stderr: '',
      exit_code: 0,
      timed_out: false,
    }

    setRunResult(nextResult)

    setEvents((prev) => [
      {
        type: 'session.run.completed',
        message: 'Python code execution completed in mock mode.',
        time: new Date().toLocaleTimeString(),
      },
      ...prev,
    ])
  }

  return (
    <main className="app">
      <header className="topbar">
        <div>
          <p className="eyebrow">Cloudterm</p>
          <h1>Real-time Algorithm Code Mentoring</h1>
          <p className="subtitle">
            Mock frontend for session creation, Python code execution results,
            line-based questions, replies, and WebSocket notifications.
          </p>
        </div>

        <div className="session-card">
          <span>Session</span>
          <strong>python-debug-session</strong>
          <small>Share URL: /sessions/mock-session-001</small>
        </div>
      </header>

      <section className="layout">
        <section className="editor-panel">
          <div className="panel-header">
            <div>
              <h2>Python Code</h2>
              <p>Mock editor screen based on docs/api-contract.md</p>
            </div>

            <button type="button" onClick={handleRunCode}>
              Run Code
            </button>
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
        </section>

        <aside className="side-panel">
          <section className="card">
            <h2>Execution Result</h2>

            <div className="result-grid">
              <div>
                <span>Exit Code</span>
                <strong>{runResult.exit_code}</strong>
              </div>
              <div>
                <span>Timed Out</span>
                <strong>{runResult.timed_out ? 'true' : 'false'}</strong>
              </div>
            </div>

            <label>stdout</label>
            <pre className="terminal success">{runResult.stdout || '(empty)'}</pre>

            <label>stderr</label>
            <pre className="terminal error">{runResult.stderr || '(empty)'}</pre>
          </section>

          <section className="card">
            <h2>WebSocket Events</h2>

            <div className="event-list">
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
            <p>
              These mock comments follow GET /sessions/{'{session_id}'}/comments
              response format.
            </p>
          </div>
        </div>

        <div className="comments-grid">
          {mockComments.map((comment) => (
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
            </article>
          ))}
        </div>
      </section>
    </main>
  )
}

export default App