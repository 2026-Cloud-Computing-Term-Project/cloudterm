# Project Status

이 문서는 `docs/team-development-guide.md` 기준으로 현재 완료된 초기 작업과 역할별 다음 행동을 고정한다.

## 초기 세팅 완료 현황

| 항목 | 상태 | 근거 |
| --- | --- | --- |
| GitHub 레포 생성 | 완료 | `https://github.com/2026-Cloud-Computing-Term-Project/cloudterm.git` |
| `main`, `dev` 브랜치 생성 | 완료 | 두 브랜치 모두 원격에 push됨 |
| 기본 폴더 구조 생성 | 완료 | `frontend/`, `backend/`, `runner/`, `infra/`, `docs/` |
| `README.md` 작성 | 완료 | 루트 온보딩 문서 |
| `.env.example` 작성 | 완료 | 공개 환경변수 이름 고정 |
| `docs/api-contract.md` 작성 | 완료 | HTTP/WebSocket/Runner API 계약 |
| 팀 개발 시작 가이드 업로드 | 완료 | `docs/team-development-guide.md` |
| 제출 산출물/수업 양식 정리 | 완료 | `docs/deliverables/`, `docs/templates/` |
| Backend/Runner 시작 의존성 파일 | 완료 | `backend/requirements.txt`, `runner/requirements.txt` |
| Frontend scaffold | 미완료 | Frontend 담당자가 feature branch에서 Vite scaffold 생성 |
| Docker Compose 전체 서비스 검증 | 부분 완료 | PostgreSQL은 실행 검증 완료, backend/frontend/runner 서비스는 아직 없음 |
| 기능 구현 | 부분 완료 | Backend/Runner 핵심 기능 구현 완료, Frontend는 별도 feature branch 진행 중 |

## 제안서 기준 정합성

제안서의 주제는 Docker 샌드박스 기반 실시간 알고리즘 코드 멘토링 플랫폼이다. 현재 초기 레포 문서는 아래 범위를 기준으로 맞춰져 있다.

- React + Monaco Editor 기반 코드 화면
- 라인별 질문/답변과 WebSocket 갱신 알림
- FastAPI API/WebSocket Server와 Runner Service 분리
- PostgreSQL에 세션, 코드 스냅샷, 질문/답변, 실행 로그 저장
- Runner가 요청마다 일회용 Docker 컨테이너를 생성해 Python 단일 파일 실행
- 프론트엔드는 Azure Static Web Apps, 백엔드/Runner/PostgreSQL은 Azure VM의 Docker Compose 기준
- Redis Queue, Kubernetes, Auto Scaling, 실시간 공동 편집, 로그인/회원가입은 초기 구현 범위에서 제외

현재 미구현으로 남은 것은 기능 코드 자체다. Frontend scaffold, Backend API scaffold, Runner service, 전체 Docker Compose 통합, Azure VM 배포 메모는 역할별 첫 작업으로 진행한다.

## 초기 통합 순서

세 역할은 동시에 시작해도 되지만, PR 통합은 아래 순서를 우선한다.

| 순서 | 담당 | 먼저 끝낼 것 | 이유 |
| --- | --- | --- | --- |
| 1 | Backend | FastAPI app, health check, 세션 API skeleton | Cloud & Infra가 compose health check와 service port를 잡을 수 있음 |
| 2 | Backend + Runner | `POST /run` skeleton, 요청/응답 모델, timeout 필드 처리 | Frontend와 Cloud & Infra가 같은 Runner 계약을 보고 작업 가능 |
| 3 | Cloud & Infra | postgres/backend/runner compose 연결, network/env/health check | 로컬 통합 실행 기준 생성 |
| 4 | Frontend | Vite scaffold, Monaco 화면, mock 기반 세션/실행 결과 UI | Backend 미완성 상태에서도 화면 작업 가능 |
| 5 | 전체 | 실제 API 연결, WebSocket 갱신, Docker Runner 실행 통합 | 중간보고서와 데모 흐름 확인 가능 |

Frontend는 1~3번이 끝날 때까지 기다리지 않는다. `docs/api-contract.md`의 필드 이름을 기준으로 mock 데이터를 먼저 만들고, Backend endpoint가 준비되면 연결만 교체한다.

## 검증 상태

| 검증 | 상태 | 비고 |
| --- | --- | --- |
| Git 초기 커밋 | 완료 | `초기 모노레포 구조 정리` |
| 원격 `main` push | 완료 | GitHub 반영됨 |
| 원격 `dev` push | 완료 | 팀원 작업 기준 브랜치 |
| `.env` 미생성 확인 | 완료 | `.env.example`만 사용 |
| Docker CLI 검증 | 완료 | Docker 설치 환경에서 compose 명령 확인 |
| `docker compose config` | 완료 | Compose YAML 구조 검증 |
| PostgreSQL 컨테이너 실행 | 완료 | `docker compose up -d postgres`, `pg_isready` 통과 |

## 역할별 지금 할 일

### Frontend

Branch:

```bash
git switch dev
git pull origin dev
git switch -c feat/frontend-editor
```

첫 작업:

- `frontend/`에 Vite React 기반 scaffold 생성
- 생성 후 `package.json`, lock file, 실행 명령을 커밋에 포함
- `VITE_API_BASE_URL`, `VITE_WS_BASE_URL` 사용 방식 고정
- 세션 생성/입장 화면과 Monaco Editor 화면 초안 작성
- API 연결 전에는 `docs/api-contract.md`의 endpoint 이름을 그대로 사용

주의:

- `docs/api-contract.md`의 endpoint를 임의로 바꾸지 않는다.
- 실행 방법이 생기면 `frontend/README.md`와 루트 `README.md`를 같이 갱신한다.

### Backend

Branch:

```bash
git switch dev
git pull origin dev
git switch -c feat/backend-api
```

첫 작업:

- `backend/requirements.txt` 기준으로 FastAPI scaffold 생성
- health check endpoint 추가
- `POST /sessions`, `GET /sessions/{session_id}`부터 구현
- PostgreSQL 연결 방식과 DB 마이그레이션 도구 사용 여부 결정
- Python 버전과 dependency pin/lock 정책 결정
- Runner 호출 URL은 `RUNNER_URL` 기준으로 사용
- Runner API 구조가 필요하면 `runner/requirements.txt` 기준으로 `POST /run` scaffold를 별도 PR 또는 같은 Backend PR의 명확한 하위 범위로 진행

현재 상태:

- 세션 생성/조회, 실행, 댓글/답글, WebSocket 알림, 실행 로그 저장 구현 완료
- Runner 내부 API 연동 및 runner 서비스 구현 완료
- 남은 핵심 과제는 마이그레이션 도입, 통합 테스트, 운영 안정화

주의:

- API 계약 변경이 필요하면 구현 전에 `docs/api-contract.md`를 먼저 갱신한다.
- DB 모델만 만들고 마이그레이션 없는 drift를 만들지 않는다.

### Cloud & Infra

Branch:

```bash
git switch dev
git pull origin dev
git switch -c feat/cloud-compose-runner
```

첫 작업:

- Docker Desktop 또는 Docker Engine 설치 환경에서 `docker compose config` 재확인
- Docker가 PATH에 없으면 Docker Desktop 실행 상태와 터미널 재시작 여부 확인
- `docker-compose.yml`에 backend, runner, postgres 연결 구조 추가
- backend/runner Dockerfile 작성 기준 결정
- Runner 컨테이너 실행 제한(timeout, memory, network, read-only)을 문서화
- Azure VM 배포 메모를 `infra/` 아래에 작성

주의:

- `.env.example` 변수 이름을 바꾸면 팀 전체 영향이 있으므로 먼저 공유한다.
- `docker compose down -v`, Docker volume 삭제는 로컬 DB 데이터를 날릴 수 있으므로 금지한다.
- Runner API 요청/응답 형식은 Backend 담당과 맞추고, Docker 제한 실행은 Cloud & Infra가 책임진다.

## 온보딩 확인 항목

새 팀원이 레포를 받은 뒤 아래 항목을 확인하면 된다.

- 기준 브랜치는 `dev`다.
- 각자 역할에 맞는 `feat/...` 브랜치를 만든다.
- 작업 전 `README.md`, `docs/project-status.md`, `docs/api-contract.md`를 확인한다.
- PostgreSQL 컨테이너 실행은 검증됐다.
- backend/frontend/runner compose 통합은 Cloud & Infra 첫 작업으로 남아 있다.
