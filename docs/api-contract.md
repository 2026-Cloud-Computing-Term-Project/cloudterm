# API Contract

이 문서는 프론트엔드, 백엔드, Runner가 동시에 개발하기 위한 초기 계약이다. 기능 구현 중 endpoint path, request/response 필드, WebSocket event 이름을 바꾸면 이 문서를 먼저 갱신한다.

## Base URLs

```text
HTTP API: http://localhost:8000
WebSocket: ws://localhost:8000
Runner internal API: http://runner:8001
```

## REST API

### POST /sessions

새 코드 실행 세션을 만든다.

Request:

```json
{
  "title": "Optional session title"
}
```

Response:

```json
{
  "session_id": "uuid",
  "title": "Optional session title",
  "share_url": "http://localhost:5173/sessions/{session_id}",
  "created_at": "2026-05-22T00:00:00Z"
}
```

### GET /sessions/{session_id}

세션 기본 정보를 조회한다.

Response:

```json
{
  "session_id": "uuid",
  "title": "Optional session title",
  "created_at": "2026-05-22T00:00:00Z"
}
```

### POST /sessions/{session_id}/run

현재 세션의 코드를 실행한다. 초기 범위는 Python 단일 파일 실행만 지원한다.

Request:

```json
{
  "language": "python",
  "code": "print('hello')",
  "stdin": ""
}
```

Response:

```json
{
  "run_id": "uuid",
  "stdout": "hello\n",
  "stderr": "",
  "exit_code": 0,
  "timed_out": false
}
```

### GET /sessions/{session_id}/comments

세션에 달린 라인별 질문과 답변 목록을 조회한다.

Response:

```json
{
  "comments": [
    {
      "comment_id": "uuid",
      "line_number": 3,
      "body": "Why does this line fail?",
      "author_name": "frontend",
      "created_at": "2026-05-22T00:00:00Z",
      "replies": [
        {
          "reply_id": "uuid",
          "body": "The variable is not defined before use.",
          "author_name": "backend",
          "created_at": "2026-05-22T00:00:00Z"
        }
      ]
    }
  ]
}
```

### POST /sessions/{session_id}/comments

특정 코드 라인에 질문을 작성한다.

Request:

```json
{
  "line_number": 3,
  "body": "Why does this line fail?",
  "author_name": "frontend"
}
```

Response:

```json
{
  "comment_id": "uuid",
  "line_number": 3,
  "body": "Why does this line fail?",
  "author_name": "frontend",
  "created_at": "2026-05-22T00:00:00Z"
}
```

### POST /sessions/{session_id}/comments/{comment_id}/replies

질문에 답변을 작성한다.

Request:

```json
{
  "body": "The variable is not defined before use.",
  "author_name": "backend"
}
```

Response:

```json
{
  "reply_id": "uuid",
  "comment_id": "uuid",
  "body": "The variable is not defined before use.",
  "author_name": "backend",
  "created_at": "2026-05-22T00:00:00Z"
}
```

## WebSocket API

### WS /ws/sessions/{session_id}

세션 단위 실시간 알림 채널이다. 초기 범위는 공동 편집이 아니라 실행 결과와 질문/답변 갱신 알림이다.

Heartbeat policy:

- 클라이언트는 연결 유지용으로 주기적으로 `"ping"` 메시지를 보낼 수 있다.
- 백엔드는 `"ping"`을 받으면 `{"type":"pong"}`으로 응답한다.
- `"pong"` 메시지는 연결 유지 확인용으로 허용한다.
- `HEARTBEAT_TIMEOUT_SECONDS` 동안 메시지가 없으면 백엔드는 연결을 종료한다.

Server events:

```json
{
  "type": "session.run.completed",
  "session_id": "uuid",
  "run_id": "uuid"
}
```

```json
{
  "type": "comment.created",
  "session_id": "uuid",
  "comment_id": "uuid"
}
```

```json
{
  "type": "reply.created",
  "session_id": "uuid",
  "comment_id": "uuid",
  "reply_id": "uuid"
}
```

## Runner Internal API

### POST http://runner:8001/run

Runner는 외부 브라우저가 직접 호출하지 않는다. 백엔드가 내부 네트워크에서 호출한다.

Request:

```json
{
  "language": "python",
  "code": "...",
  "stdin": "",
  "timeout_seconds": 3
}
```

Response:

```json
{
  "stdout": "...",
  "stderr": "...",
  "exit_code": 0,
  "timed_out": false
}
```

초기 구현 범위는 Python 단일 파일 실행이다. C/C++ 등 다른 언어는 Runner 이미지를 추가하는 확장으로만 다룬다.
