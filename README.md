# Cloudterm

클라우드컴퓨팅 텀 프로젝트 모노레포다. 팀원은 이 문서를 먼저 보고, 상세 운영 규칙은 `docs/team-development-guide.md`, 현재 완료/다음 작업은 `docs/project-status.md`를 확인한다.

## 지금 상태

- GitHub repo, `main`, `dev` 브랜치 생성 완료
- 초기 모노레포 폴더와 기본 문서 생성 완료
- API 계약과 환경변수 이름 고정 완료
- 백엔드 core 기능과 runner API 구현 완료
- `docker-compose.yml`은 PostgreSQL, backend, runner 서비스를 포함함
- `docker compose config` 검증 완료
- `docker compose up -d postgres`와 PostgreSQL readiness 검증 완료

## 제안서 기준 범위

- 주제: Docker 샌드박스 기반 실시간 알고리즘 코드 멘토링 플랫폼
- 프론트엔드: React, Monaco Editor, 라인별 질문/답변 UI, WebSocket 알림
- 백엔드: FastAPI API/WebSocket Server, PostgreSQL 저장, Runner 내부 API 호출
- Runner: 요청마다 일회용 Docker 컨테이너를 생성해 Python 단일 파일 코드를 격리 실행
- 배포 기준: 프론트엔드는 Azure Static Web Apps, 백엔드/Runner/PostgreSQL은 Azure VM의 Docker Compose
- 제외 범위: 로그인/회원가입, 실시간 공동 편집, Kubernetes, Redis Queue, Auto Scaling

## 팀원이 처음 할 일

```bash
git clone https://github.com/2026-Cloud-Computing-Term-Project/cloudterm.git
cd cloudterm
git switch dev
```

역할별 브랜치:

```bash
git switch -c feat/frontend-editor
git switch -c feat/backend-api
git switch -c feat/cloud-compose-runner
```

작업 시작 전 반드시 확인할 파일:

1. `docs/project-status.md`
2. `docs/team-development-guide.md`
3. `docs/api-contract.md`
4. `.env.example`
5. 본인 담당 폴더의 `README.md`

## 프로젝트 구조

```text
cloudterm/
  frontend/          # React, Monaco Editor, WebSocket client
  backend/           # FastAPI API, WebSocket, DB model
  runner/            # 사용자 코드 실행 Runner service
  infra/             # Azure VM, Nginx, firewall, deployment docs/scripts
  docs/
    README.md
    api-contract.md
    project-status.md
    team-development-guide.md
    deliverables/
    templates/
  docker-compose.yml
  .env.example
  .gitignore
  .gitattributes
  .editorconfig
  README.md
```

루트에는 개발자가 바로 봐야 하는 프로젝트 운영 문서와 실행 파일만 둔다. 제안서, 중간보고서, 최종보고서, 발표자료 같은 제출 산출물은 `docs/deliverables/`, 수업 제공 양식은 `docs/templates/`에 둔다.

## 역할별 첫 목표

| 역할 | 첫 브랜치 | 첫 작업 |
| --- | --- | --- |
| Frontend | `feat/frontend-editor` | Vite React scaffold, 세션 입장 화면, Monaco Editor 기반 편집 화면 초안 |
| Backend | `feat/backend-api` | FastAPI scaffold, health check, 세션/API 계약 구현 시작 |
| Cloud & Infra | `feat/cloud-compose-runner` | Docker Compose 검증, backend/runner/postgres 서비스 구성, Runner 실행 제한 설계 |

`runner/`는 공동 영역이다. Runner API 요청/응답 형식은 Backend가 잡고, Runner 컨테이너 실행 제한과 배포 환경은 Cloud & Infra가 잡는다.

## 초기 작업 순서

완전한 순차 진행은 아니다. 세 역할이 동시에 시작하되, 아래 순서로 합쳐야 덜 막힌다.

| 순서 | 담당 | 완료 기준 | 다음 담당에게 풀리는 것 |
| --- | --- | --- | --- |
| 1 | Backend | FastAPI app, health check, 세션 API skeleton | Cloud & Infra가 backend service를 compose에 연결 가능 |
| 2 | Backend + Runner | `POST /run` skeleton과 요청/응답 모델 | Frontend가 실행 결과 연동 가능, Cloud & Infra가 runner service를 compose에 연결 가능 |
| 3 | Cloud & Infra | postgres/backend/runner compose 연결과 health check | Backend/Runner를 같은 compose network에서 검증 가능 |
| 4 | Frontend | Vite/React/Monaco 화면과 mock 상태 | Backend API가 준비되는 즉시 실제 API로 교체 가능 |
| 5 | 전체 | 세션 생성, 코드 실행, 질문/답변, WebSocket 흐름 통합 | 중간보고서와 데모 시나리오 작성 가능 |

Frontend는 Backend를 기다리지 말고 `docs/api-contract.md` 기준 mock으로 화면을 먼저 만든다. Backend와 Cloud & Infra는 health check와 포트부터 맞춘 뒤 Runner 제한 실행을 붙인다.

## 로컬 준비

환경변수 이름은 `.env.example`을 기준으로 맞춘다. 실제 `.env`는 Git에 올리지 않는다.

```powershell
Copy-Item .env.example .env
```

현재 `docker-compose.yml`은 초기 구조 단계라 PostgreSQL만 정의한다. frontend/backend/runner 서비스는 각 영역의 Dockerfile과 health check가 생긴 뒤 추가한다.

```powershell
docker compose up -d postgres
docker compose exec postgres pg_isready -U cloudterm -d cloudterm
```

Docker 명령이 인식되지 않으면 Docker Desktop을 설치하거나 PATH를 확인한다.

```powershell
winget install -e --id Docker.DockerDesktop
```

설치 직후에도 `docker` 명령이 안 잡히면 새 터미널을 열거나 Docker Desktop이 실행 중인지 확인한다.

## API 계약

초기 API 경로와 Runner 내부 API는 `docs/api-contract.md`를 기준으로 한다. 프론트엔드와 백엔드가 동시에 작업할 수 있도록 endpoint path, request/response 필드, WebSocket event 이름을 변경할 때는 해당 문서를 먼저 갱신한다.

## 브랜치 규칙

```text
main                  # 제출 가능한 안정 버전
dev                   # 통합 개발 브랜치
feat/frontend-*       # 프론트엔드 작업
feat/backend-*        # 백엔드 작업
feat/cloud-*          # 클라우드/Runner/배포 작업
docs/*                # 보고서, 발표자료, 데모 문서 작업
```

- `main`에 직접 push하지 않는다.
- 각자 `feat/...` 브랜치에서 작업한 뒤 PR로 `dev`에 합친다.
- 실행 방법, 환경변수, API 계약이 바뀌면 관련 README 또는 `docs/api-contract.md`도 같이 갱신한다.

## 저장소 기본 설정 파일

- `.editorconfig`: 에디터가 들여쓰기, LF 줄바꿈, 마지막 newline 규칙을 맞추도록 한다.
- `.gitattributes`: Git이 텍스트 파일 줄바꿈은 LF로, 이미지/PDF/DOCX는 binary로 다루도록 한다.

이 두 파일은 팀원 OS와 에디터가 달라도 쓸데없는 줄바꿈 diff가 생기지 않게 하는 장치다.
