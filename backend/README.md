# Backend

백엔드 담당 영역이다.

초기 책임:

- FastAPI HTTP API
- 세션 생성/조회 API
- 코드 실행 요청 API
- 질문/답변 API
- WebSocket room 관리
- PostgreSQL 연동
- Runner 내부 API 호출

기능 구현 전 `docs/api-contract.md`와 `.env.example`의 `DATABASE_URL`, `RUNNER_URL`, `RUN_TIMEOUT_SECONDS`를 먼저 확인한다.

현재는 시작 시 Alembic으로 최신 스키마까지 마이그레이션을 적용한다.
WebSocket 세션 채널은 heartbeat 용도로 `"ping"`/`"pong"` 메시지를 지원하고, 일정 시간 동안 입력이 없으면 연결을 종료한다.

현재 구현 범위:

- `GET /health`
- `POST /sessions`
- `GET /sessions/{session_id}`
- `POST /sessions/{session_id}/run`
- `GET /sessions/{session_id}/runs`
- `GET /sessions/{session_id}/comments`
- `POST /sessions/{session_id}/comments`
- `POST /sessions/{session_id}/comments/{comment_id}/replies`
- `WS /ws/sessions/{session_id}`
- PostgreSQL 세션/실행/댓글/답글 저장
- 실행 이력 조회와 실행 당시 코드 스냅샷 반환
- Runner 내부 API 연동

## 첫 작업

```bash
git switch dev
git pull origin dev
git switch -c feat/backend-api
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

초기 구현 순서:

1. FastAPI app scaffold
2. health check endpoint
3. `POST /sessions`
4. `GET /sessions/{session_id}`
5. Runner 호출 client
6. PostgreSQL 연결과 마이그레이션 방식 결정

`requirements.txt`는 시작용 의존성 목록이다. 실제 scaffold와 테스트가 확인된 뒤 필요하면 버전 pin 또는 lock 파일을 추가한다.
