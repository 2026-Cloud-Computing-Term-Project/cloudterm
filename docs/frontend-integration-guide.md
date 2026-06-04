# Frontend Integration Guide

이 문서는 프론트엔드 담당자가 mock UI를 실제 backend와 연결할 때 참고할 실행 기준을 정리한다. API path와 request/response 필드는 `docs/api-contract.md`가 SSoT다.

## 현재 Cloud/Infra 상태

- Azure backend stack 배포 검증 완료
- Resource group: `cloudterm-rg`
- VM: `cloudterm-vm`
- Region: Korea Central
- Backend public endpoint: `http://52.231.65.10:8000`
- Backend health: `GET /health`
- Runner와 PostgreSQL은 외부에서 직접 접근하지 않음
- Runner 내부 API는 backend가 Docker Compose network에서만 호출함
- 현재 VM은 배포 검증 후 비용 절감을 위해 deallocate 상태일 수 있음

VM이 deallocate 상태이면 Azure backend endpoint는 응답하지 않는다. 이 경우 프론트 작업은 mock 데이터나 로컬 `docker compose up --build` backend 기준으로 진행한다.

## Frontend 환경변수

로컬 backend 기준:

```text
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_BASE_URL=ws://localhost:8000
```

현재 검증된 Azure VM backend 기준:

```text
VITE_API_BASE_URL=http://52.231.65.10:8000
VITE_WS_BASE_URL=ws://52.231.65.10:8000
```

Azure Static Web Apps처럼 HTTPS에서 프론트가 뜨면 브라우저 mixed content 정책 때문에 `http://`와 `ws://` 연결이 차단될 수 있다. 그 경우 backend 앞에 HTTPS reverse proxy를 붙인 뒤 아래처럼 바꾼다.

```text
VITE_API_BASE_URL=https://<BACKEND_DOMAIN>
VITE_WS_BASE_URL=wss://<BACKEND_DOMAIN>
```

## 연결 순서

1. `VITE_API_BASE_URL`과 `VITE_WS_BASE_URL`을 읽는 frontend API client를 만든다.
2. 세션 생성 화면에서 `POST /sessions`를 호출한다.
3. 생성된 `session_id`로 `/sessions/{session_id}` 화면을 연다.
4. 세션 화면 진입 시 `GET /sessions/{session_id}`와 `GET /sessions/{session_id}/comments`를 호출한다.
5. 실행 버튼은 `POST /sessions/{session_id}/run`을 호출하고 `stdout`, `stderr`, `exit_code`, `timed_out`을 결과 패널에 표시한다.
6. 라인별 질문 작성은 `POST /sessions/{session_id}/comments`를 호출한다.
7. 답변 작성은 `POST /sessions/{session_id}/comments/{comment_id}/replies`를 호출한다.
8. 세션 화면 진입 후 `WS /ws/sessions/{session_id}`에 연결해서 갱신 이벤트를 받는다.
9. WebSocket 이벤트를 받으면 필요한 REST endpoint를 다시 호출해서 화면 데이터를 갱신한다.

## WebSocket 처리 기준

프론트는 아래 server event를 받을 수 있어야 한다.

```json
{ "type": "session.run.completed", "session_id": "uuid", "run_id": "uuid" }
```

```json
{ "type": "comment.created", "session_id": "uuid", "comment_id": "uuid" }
```

```json
{ "type": "reply.created", "session_id": "uuid", "comment_id": "uuid", "reply_id": "uuid" }
```

권장 처리:

- `session.run.completed`: 실행 결과 표시 영역을 최신 상태로 갱신
- `comment.created`: 댓글 목록 재조회
- `reply.created`: 댓글 목록 재조회
- 연결 유지가 필요하면 `"ping"`을 보내고 `{"type":"pong"}` 응답을 허용
- WebSocket이 끊기면 화면이 죽지 않게 REST 재조회 버튼이나 자동 재연결을 둠

## 프론트가 직접 호출하지 않는 것

- `runner` service
- `http://runner:8001`
- PostgreSQL
- Docker socket
- Azure VM SSH

브라우저는 backend만 호출한다. Runner 실행과 DB 저장은 backend 책임이다.

## 최소 완료 기준

- `.env` 또는 배포 환경변수로 API/WS base URL을 바꿀 수 있음
- `POST /sessions`로 세션 생성 가능
- `POST /sessions/{session_id}/run` 결과가 Monaco 화면 옆 결과 패널에 표시됨
- 댓글/답글 작성 후 목록이 갱신됨
- WebSocket 이벤트 수신 시 화면이 갱신됨
- Azure VM backend가 켜져 있을 때 `http://52.231.65.10:8000/health` 기준으로 실제 API 연결 검증 가능
- HTTPS 프론트 배포에서 mixed content가 발생하면 Cloud/Infra에 HTTPS/WSS reverse proxy 필요를 공유함
