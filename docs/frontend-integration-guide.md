# Frontend Integration Guide

이 문서는 프론트엔드가 실제 backend와 연결되는 기준을 정리한다. API path와 request/response 필드는 `docs/api-contract.md`가 SSoT다.

## 현재 Cloud/Infra 상태

- Azure backend stack 배포 검증 완료
- Resource group: `cloudterm-rg`
- VM: `cloudterm-vm`
- Region: Korea Central
- Backend public endpoint: `https://cloudterm-backend-3.koreacentral.cloudapp.azure.com`
- Frontend public endpoint: `https://yellow-field-0ad776800.7.azurestaticapps.net`
- Backend health: `GET /health`
- Runner와 PostgreSQL은 외부에서 직접 접근하지 않음
- Runner 내부 API는 backend가 Docker Compose network에서만 호출함
- 현재 VM은 공개 데모를 위해 실행 상태일 수 있으며, 비용 절감을 위해 deallocate하면 backend endpoint는 응답하지 않음

VM이 deallocate 상태이면 Azure backend endpoint는 응답하지 않는다. 이 경우 공개 Static Web Apps 화면은 열릴 수 있지만 세션 생성, 코드 실행, WebSocket 기능은 실패한다. 프론트 기능 검증은 VM을 다시 시작하거나 로컬 `docker compose up --build` backend 기준으로 진행한다.

## Frontend 환경변수

로컬 backend 기준:

```text
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_BASE_URL=ws://localhost:8000
```

현재 검증된 Azure 공개 배포 기준:

```text
VITE_API_BASE_URL=https://cloudterm-backend-3.koreacentral.cloudapp.azure.com
VITE_WS_BASE_URL=wss://cloudterm-backend-3.koreacentral.cloudapp.azure.com
```

Azure Static Web Apps workflow는 위 값을 build 환경변수로 주입한다. HTTPS 프론트에서 `http://`와 `ws://` backend를 직접 호출하면 브라우저 mixed content 정책 때문에 차단된다.

Backend VM `.env`의 `FRONTEND_BASE_URL`도 공개 프론트 URL과 맞아야 한다.

```text
FRONTEND_BASE_URL=https://yellow-field-0ad776800.7.azurestaticapps.net
```

## 연결 순서

1. `VITE_API_BASE_URL`과 `VITE_WS_BASE_URL`을 읽는 frontend API client를 만든다.
2. 세션 생성 화면에서 `POST /sessions`를 호출한다.
3. 생성된 `session_id`로 `/sessions/{session_id}` 화면을 연다.
4. 세션 화면 진입 시 `GET /sessions/{session_id}`, `GET /sessions/{session_id}/runs`, `GET /sessions/{session_id}/comments`를 호출한다.
5. 실행 버튼은 `POST /sessions/{session_id}/run`을 호출하고 `stdout`, `stderr`, `exit_code`, `timed_out`을 결과 패널에 표시한다.
6. 실행 이력에서 run을 선택하면 해당 run의 코드 스냅샷과 실행 결과를 복원한다.
7. 라인별 질문 작성은 `POST /sessions/{session_id}/comments`를 호출한다.
8. 답변 작성은 `POST /sessions/{session_id}/comments/{comment_id}/replies`를 호출한다.
9. 세션 화면 진입 후 `WS /ws/sessions/{session_id}`에 연결해서 갱신 이벤트를 받는다.
10. WebSocket 이벤트를 받으면 필요한 REST endpoint를 다시 호출해서 화면 데이터를 갱신한다.

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

- `session.run.completed`: 실행 이력과 실행 결과 표시 영역을 최신 상태로 갱신
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
- `GET /sessions/{session_id}/runs`로 실행 이력을 불러오고 코드 스냅샷을 복원할 수 있음
- 댓글/답글 작성 후 목록이 갱신됨
- WebSocket 이벤트 수신 시 화면이 갱신됨
- Azure VM backend가 켜져 있을 때 `https://cloudterm-backend-3.koreacentral.cloudapp.azure.com/health` 기준으로 실제 API 연결 검증 가능
- Azure Static Web Apps 공개 URL에서 세션 생성, 코드 실행, 댓글/답글, WebSocket 이벤트, 실행 이력 복원 검증 가능
