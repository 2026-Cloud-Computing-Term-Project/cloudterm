const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '/api'

const defaultWsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'

export const WS_BASE_URL =
  import.meta.env.VITE_WS_BASE_URL ?? `${defaultWsProtocol}//${window.location.host}`

export type Session = {
  session_id: string
  title: string
  share_url?: string
  created_at: string
}

export type RunResult = {
  run_id: string
  stdout: string
  stderr: string
  exit_code: number
  timed_out: boolean
}

export type Reply = {
  reply_id: string
  comment_id?: string
  body: string
  author_name: string
  created_at: string
}

export type Comment = {
  comment_id: string
  line_number: number
  body: string
  author_name: string
  created_at: string
  replies: Reply[]
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
  })

  if (!response.ok) {
    const text = await response.text()
    throw new Error(text || `Request failed with status ${response.status}`)
  }

  return response.json() as Promise<T>
}

export function createSession(title: string) {
  return request<Session>('/sessions', {
    method: 'POST',
    body: JSON.stringify({ title }),
  })
}

export function getSession(sessionId: string) {
  return request<Session>(`/sessions/${sessionId}`)
}

export function runCode(sessionId: string, code: string, stdin = '') {
  return request<RunResult>(`/sessions/${sessionId}/run`, {
    method: 'POST',
    body: JSON.stringify({
      language: 'python',
      code,
      stdin,
    }),
  })
}

export function getComments(sessionId: string) {
  return request<{ comments: Comment[] }>(`/sessions/${sessionId}/comments`)
}

export function createComment(
  sessionId: string,
  lineNumber: number,
  body: string,
  authorName: string,
) {
  return request<Comment>(`/sessions/${sessionId}/comments`, {
    method: 'POST',
    body: JSON.stringify({
      line_number: lineNumber,
      body,
      author_name: authorName,
    }),
  })
}

export function createReply(
  sessionId: string,
  commentId: string,
  body: string,
  authorName: string,
) {
  return request<Reply>(`/sessions/${sessionId}/comments/${commentId}/replies`, {
    method: 'POST',
    body: JSON.stringify({
      body,
      author_name: authorName,
    }),
  })
}