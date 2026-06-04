# 팀 개발 시작 가이드

현재 완료 현황과 역할별 바로 다음 작업은 `docs/project-status.md`를 기준으로 한다. 이 문서는 브랜치 전략, 역할 분담, PR 규칙, 구현 범위를 설명하는 상세 가이드다.

## 기본 방향

이 프로젝트는 **하나의 GitHub 레포에서 모노레포 방식으로 진행**한다.

프론트엔드, 백엔드, 클라우드/인프라가 따로 떨어진 프로젝트가 아니라 `frontend`, `backend`, `runner`, `postgres`, `docker-compose`가 함께 동작해야 하는 시스템이므로 레포를 나누지 않는다. 레포를 나누면 merge conflict는 줄어들 수 있지만, 최종 통합과 배포에서 더 큰 문제가 생긴다.

## 추천 레포 구조

```text
cloudterm/
  frontend/          # React, Monaco Editor, WebSocket client
  backend/           # FastAPI API, WebSocket, DB 모델
  runner/            # 사용자 코드 실행 Runner Service
  infra/             # Azure VM 배포 문서, Nginx, 방화벽, 운영 스크립트
  docs/              # 개발 문서, 제출 산출물, 수업 양식
    deliverables/    # 제안서, 중간보고서, 최종보고서, 발표자료
    templates/       # 수업 제공 양식과 공지 원본
  docker-compose.yml
  .env.example
  README.md
```

## 역할 분담

| 역할 | 주 담당 영역 | 주요 책임 |
| --- | --- | --- |
| 프론트엔드 | `frontend/` | 세션 생성/입장 화면, Monaco Editor, 실행 버튼, 결과 창, 라인별 질문/답변 UI, WebSocket 알림 표시 |
| 백엔드 | `backend/` | FastAPI, 세션 API, 질문/답변 API, 실행 로그 API, WebSocket room 관리, PostgreSQL 연동 |
| 클라우드/인프라 | `infra/`, `docker-compose.yml`, `.env.example` | Docker Compose, Azure VM 배포, 포트/CORS/환경변수 관리, Docker 실행 제한 설정 |

`runner/`는 공동 영역이다. 역할을 아래처럼 나눈다.

| 영역 | 담당 |
| --- | --- |
| Runner API 구조, 요청/응답 형식, stdout/stderr/exit code 처리 | 백엔드 담당 |
| Runner Dockerfile, 샌드박스 컨테이너 실행 옵션, timeout/memory/CPU/network/read-only/non-root 제한 | 클라우드/인프라 담당 |

즉, 백엔드 담당자는 Runner가 어떤 API로 동작할지 정하고, 클라우드/인프라 담당자는 그 Runner가 실제 Docker 샌드박스를 안전하게 실행하도록 만든다.

## 브랜치 전략

```text
main                  # 제출 가능한 안정 버전
dev                   # 통합 개발 브랜치
feat/frontend-*       # 프론트엔드 작업
feat/backend-*        # 백엔드 작업
feat/cloud-*          # 클라우드/Runner/배포 작업
docs/*                # 보고서, 발표자료, 데모 문서 작업
```

규칙:

- `main`에 직접 push하지 않는다.
- `dev`는 원칙적으로 PR로 합친다.
- 단, 초기 폴더 생성, README 초안, 문서 정리처럼 가벼운 작업은 사전에 공유한 뒤 `dev`에 직접 push할 수 있다.
- 각자 `feat/...` 브랜치에서 작업한 뒤 GitHub PR로 `dev`에 합친다.
- 데모 가능한 상태가 되면 `dev`를 `main`으로 merge한다.
- 하루에 한 번 이상 `dev`에 통합한다. 데모 전날 처음 합치지 않는다.

## 작업 시작 순서

### 1. 초기 구조 생성

처음 30분에서 1시간은 한 명이 기본 구조만 만든다.

```text
frontend/
backend/
runner/
infra/
docs/
docker-compose.yml
.env.example
README.md
```

이 초기 커밋 이후 각자 브랜치를 판다.

### 2. 팀원 초대 전 완료 조건

팀원 초대는 아래 작업이 끝난 뒤 진행한다.

- GitHub 레포 생성
- `main`, `dev` 브랜치 생성
- 기본 폴더 구조 생성
- `README.md` 작성
- `.env.example` 작성
- `docs/api-contract.md` 작성
- `docs/team-development-guide.md` 업로드

이 단계에서는 기능 구현까지 할 필요는 없다. 팀원이 들어왔을 때 어디에 무엇을 만들지, 어떤 브랜치에서 작업할지, 어떤 API와 환경변수 이름을 쓸지만 고정되어 있으면 된다.

### 3. 공통 계약 먼저 고정

프론트와 백엔드가 동시에 개발하려면 API 계약이 먼저 필요하다. 아래 정도는 초기에 고정한다.

API 계약은 아래 파일에 기록한다.

```text
docs/api-contract.md
```

```text
POST /sessions
GET /sessions/{session_id}
POST /sessions/{session_id}/run
GET /sessions/{session_id}/comments
POST /sessions/{session_id}/comments
POST /sessions/{session_id}/comments/{comment_id}/replies
WS /ws/sessions/{session_id}
```

Runner 내부 API도 고정한다.

```text
POST http://runner:8001/run

Request:
{
  "language": "python",
  "code": "...",
  "stdin": "",
  "timeout_seconds": 3
}

Response:
{
  "stdout": "...",
  "stderr": "...",
  "exit_code": 0,
  "timed_out": false
}
```

초기 구현 범위는 **Python 단일 파일 실행**으로 제한한다. C/C++ 등 다른 언어는 Runner 이미지를 추가하는 확장 방향으로만 둔다.

### 4. 환경변수 규칙 정하기

환경변수 이름이 흔들리면 프론트, 백엔드, Docker Compose가 계속 어긋난다. 초기에 `.env.example`을 만들고 아래 값은 고정한다.

```text
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_BASE_URL=ws://localhost:8000
DATABASE_URL=postgresql://cloudterm:cloudterm@postgres:5432/cloudterm
RUNNER_URL=http://runner:8001
RUN_TIMEOUT_SECONDS=3
```

규칙:

- 실제 비밀번호나 Azure 키는 `.env`에만 둔다.
- `.env`는 Git에 올리지 않는다.
- `.env.example`은 Git에 올린다.
- 환경변수를 추가하거나 이름을 바꿀 때는 클라우드/인프라 담당자에게 먼저 말한다.

### 5. 팀원 초대 후 첫 행동

팀원이 초대받으면 바로 기능 구현부터 시작하지 않고, 먼저 아래를 확인한다.

- `README.md` 읽기
- `docs/project-status.md` 읽기
- `docs/team-development-guide.md` 읽기
- `docs/api-contract.md` 읽기
- `.env.example` 확인
- 본인 역할과 담당 폴더 확인
- `dev` 브랜치를 기준으로 본인 작업 브랜치 생성

팀원 초대 직후에는 각자 맡은 영역의 1차 목표만 잡는다. 처음부터 전체 기능을 끝내려고 하지 않는다.

### 6. 각자 브랜치 생성

```bash
git switch dev
git pull origin dev
git switch -c feat/frontend-editor
```

백엔드:

```bash
git switch dev
git pull origin dev
git switch -c feat/backend-api
```

클라우드/인프라:

```bash
git switch dev
git pull origin dev
git switch -c feat/cloud-compose-runner
```

## 초기 병렬 작업 순서

세 역할은 동시에 시작하지만, 의존성은 있다. “누가 먼저 일을 시작하느냐”가 아니라 “어떤 PR이 먼저 합쳐져야 다음 통합이 쉬운가”를 기준으로 본다.

| 순서 | 담당 | 산출물 | 의존/해제 관계 |
| --- | --- | --- | --- |
| 1 | 백엔드 | FastAPI app, `/health`, 세션 API skeleton | 클라우드/인프라가 backend 컨테이너 port와 health check를 고정할 수 있다. |
| 2 | 백엔드 + Runner | Runner `POST /run` skeleton, 요청/응답 모델, timeout 처리 자리 | 프론트엔드는 실행 결과 타입을 맞출 수 있고, 클라우드/인프라는 runner service를 compose에 올릴 수 있다. |
| 3 | 클라우드/인프라 | postgres/backend/runner compose 연결, env, network, health check | 백엔드와 Runner를 같은 로컬 compose 환경에서 검증할 수 있다. |
| 4 | 프론트엔드 | Vite scaffold, Monaco 화면, mock 기반 세션/실행 결과/질문 UI | 백엔드 API가 준비되면 mock adapter를 실제 API 호출로 교체하면 된다. |
| 5 | 전체 | 실제 API 연결, WebSocket 갱신, Docker Runner 실행 통합 | 중간보고서와 최종 데모의 핵심 흐름을 확인할 수 있다. |

프론트엔드는 백엔드가 끝날 때까지 기다리면 안 된다. `docs/api-contract.md` 기준으로 mock 데이터를 먼저 만들고, endpoint가 준비되면 연결부만 바꾼다.

클라우드/인프라는 backend/runner 구현을 기다리는 동안 Docker Desktop/Engine, PostgreSQL compose, `.env.example`, 포트 정책, Dockerfile 작성 기준을 먼저 잡는다. 단, 전체 compose 통합 PR은 backend/runner에 최소 app entrypoint와 health check가 생긴 뒤 합치는 편이 안전하다.

## 충돌 방지 규칙

충돌이 잘 나는 파일은 한 명이 소유한다.

| 파일/영역 | Owner |
| --- | --- |
| `frontend/` | 프론트 담당 |
| `backend/` | 백엔드 담당 |
| `runner/` API 코드 | 백엔드 담당 |
| `runner/` Docker 실행 환경 | 클라우드/인프라 담당 |
| `infra/` | 클라우드/인프라 담당 |
| `docker-compose.yml` | 클라우드/인프라 담당 |
| `.env.example` | 클라우드/인프라 담당 |
| `docs/api-contract.md` | 백엔드 담당 |
| `README.md` | 클라우드/인프라 담당 또는 팀장 |
| `docs/` | 보고서 작성 담당자가 수정하되, 발표 직전에는 한 명만 편집 |

공통 파일을 수정해야 할 때는 팀 공용 채널에 먼저 알린다.

예:

```text
docker-compose.yml에 backend env 하나 추가해야 함. cloud 담당자가 반영 가능?
```

## PR 규칙

좋은 PR은 작다.

좋은 예:

```text
feat: add session create api
feat: add editor layout
feat: add docker runner endpoint
feat: connect run button to api
infra: add postgres service to compose
docs: add demo scenario
```

나쁜 예:

```text
feat: implement all frontend
feat: implement backend
feat: finish project
```

PR 전에 확인할 것:

- 내 브랜치가 최신 `dev`를 반영했는가?
- 내 역할 영역 밖 파일을 수정했는가?
- 수정했다면 owner에게 말했는가?
- 실행 방법이나 환경변수가 바뀌었다면 README 또는 `.env.example`도 맞췄는가?

최신 `dev` 반영:

```bash
git switch feat/frontend-editor
git fetch origin
git merge origin/dev
```

Git에 익숙한 사람만 rebase를 사용한다.

```bash
git switch feat/frontend-editor
git fetch origin
git rebase origin/dev
```

## 1차 목표

처음 목표는 완성품이 아니라 **로컬에서 Docker Compose로 전체 서비스가 뜨는 상태**다.

```bash
docker compose up --build
```

성공 기준:

- 프론트엔드 화면 접속 가능
- 백엔드 health check 가능
- PostgreSQL 연결 가능
- Runner Service health check 가능
- API에서 Runner로 실행 요청 가능
- Python 코드 실행 결과가 stdout/stderr로 반환됨

역할별 1차 완료 기준:

| 역할 | 1차 완료 기준 |
| --- | --- |
| 프론트엔드 | mock 데이터 또는 임시 API로 세션 입장 화면, Monaco Editor, 실행 결과 패널이 보인다. |
| 백엔드 | Swagger 또는 curl로 세션 생성, 실행 요청, 질문/답변 API, WebSocket 연결이 확인된다. |
| 클라우드/인프라 | `docker compose up --build`로 frontend/backend/runner/postgres가 뜨고, 각 서비스 health check가 가능하다. |
| Runner | Python 코드를 받아 stdout/stderr/exit code/timed_out 형식으로 결과를 반환한다. |

## 2차 목표

멘토링 흐름이 보이는 데모를 만든다.

성공 기준:

- 세션 생성
- 공유 링크로 같은 세션 입장
- 코드 작성
- 실행 요청
- 정상 실행 결과 표시
- 오류 코드 stderr 표시
- 무한 루프 timeout 처리
- 특정 라인에 질문 작성
- 답변 작성
- WebSocket으로 같은 세션 사용자에게 갱신 알림

## 최종 데모에서 반드시 보여줄 것

제안서의 핵심은 “클라우드에 배포했다”가 아니라 **신뢰할 수 없는 사용자 코드를 Docker 컨테이너에서 격리 실행한다**는 점이다.

따라서 데모 영상에는 아래 장면이 들어가야 한다.

- Azure VM 또는 서버에서 Docker Compose로 서비스 실행
- 사용자가 브라우저에서 코드 실행 요청
- Runner Service가 일회용 Docker 컨테이너 실행
- 정상 코드 stdout 반환
- 오류 코드 stderr 반환
- 무한 루프 timeout 처리
- 실행 후 컨테이너가 삭제되는 로그
- 질문/답변이 WebSocket으로 갱신되는 화면

## 구현 범위 제한

이번 프로젝트에서 하지 않는 것:

- 로그인/회원가입
- 권한 관리
- 실시간 공동 편집
- 여러 언어 동시 지원
- Kubernetes
- Redis Queue
- Auto Scaling
- 프로덕션 수준 보안 샌드박스

이번 프로젝트에서 하는 것:

- 세션 링크 기반 입장
- Python 단일 파일 실행
- API / Runner 분리
- Docker 제한 실행
- PostgreSQL 저장
- WebSocket 알림
- Docker Compose 기반 배포

## 하루 작업 루틴

작업 시작:

```bash
git switch dev
git pull origin dev
git switch feat/my-task
git merge dev
```

작업 중:

```bash
git status
git add <files>
git commit -m "feat: add ..."
```

작업 종료:

```bash
git push origin feat/my-task
```

GitHub에서 PR 생성:

```text
base: dev
compare: feat/my-task
```

## 중간보고서용 진행 상황 정리 기준

중간 결과 보고에는 “무엇을 만들었는지”보다 “제안서 구조가 실제로 구현되고 있는지”가 보이게 작성한다.

예:

```text
프론트엔드: 세션 입장 화면과 Monaco Editor 기반 코드 작성 화면 구현 중
백엔드: 세션 API, 실행 요청 API, WebSocket room 구조 구현 중
클라우드/인프라: Docker Compose 기반 API/Runner/PostgreSQL 실행 환경 구성 중
Runner: Python 코드 실행 요청을 받아 일회용 Docker 컨테이너에서 실행하는 흐름 구현 중
```

## 결론

3명이 active하게 작업해도 하나의 레포에서 진행하는 것이 맞다. 대신 파일 소유권을 분명히 하고, 공통 파일은 owner가 관리하며, PR을 작게 쪼개야 한다. 이 방식이면 merge conflict는 생겨도 통제 가능한 수준으로 줄일 수 있고, 최종 제출에 필요한 통합 비용도 낮출 수 있다.
