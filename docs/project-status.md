# Project Status

이 문서는 제안서 기준 구현 상태와 제출 전 검증 상태를 고정한다. 초기 개발 절차는 `docs/team-development-guide.md`를 참고하고, 최종 제출 보고서는 루트 `README.md`와 `docs/deliverables/report.pdf`를 기준으로 한다.

## 초기 세팅 완료 현황

| 항목 | 상태 | 근거 |
| --- | --- | --- |
| GitHub 레포 생성 | 완료 | `https://github.com/2026-Cloud-Computing-Term-Project/cloudterm.git` |
| `main`, `dev` 브랜치 생성 | 완료 | 두 브랜치 모두 원격에 push됨 |
| 기본 폴더 구조 생성 | 완료 | `frontend/`, `backend/`, `runner/`, `infra/`, `docs/` |
| `README.md` 작성 | 완료 | 최종보고서 원본 |
| `.env.example` 작성 | 완료 | 공개 환경변수 이름 고정 |
| `docs/api-contract.md` 작성 | 완료 | HTTP/WebSocket/Runner API 계약 |
| Frontend 연동 가이드 작성 | 완료 | `docs/frontend-integration-guide.md`에 실제 backend 연결 순서와 Azure VM 기준 정리 |
| 팀 개발 시작 가이드 업로드 | 완료 | `docs/team-development-guide.md` |
| 제출 산출물/수업 양식 정리 | 완료 | `docs/deliverables/`, `docs/templates/` |
| Backend/Runner 시작 의존성 파일 | 완료 | `backend/requirements.txt`, `runner/requirements.txt` |
| Frontend 구현 | 완료 | `frontend/` Vite React TypeScript, Monaco Editor, 실제 REST/WebSocket 연동, 실행 이력/코드 스냅샷 복원 UI |
| Docker Compose 전체 서비스 검증 | 완료 | 빈 DB 기준 backend/runner/postgres compose smoke test 통과 |
| Azure VM backend stack 배포 | 완료 | `cloudterm-rg`의 `cloudterm-vm`에서 backend/runner/postgres compose 배포, Caddy HTTPS/WSS reverse proxy, 외부 health 검증 완료 |
| Azure Static Web Apps 공개 배포 | 완료 | `https://yellow-field-0ad776800.7.azurestaticapps.net` 기준 공개 프론트 배포와 HTTPS/WSS backend 연동 검증 완료 |
| Cloud/Infra 배포 증거 정리 | 완료 | `infra/evidence.md`에 Azure 리소스, 검증 결과, 재검증 체크리스트 정리 |
| 기능 구현 | 완료 | 세션 생성, 코드 실행, 실행 이력, 코드 스냅샷 복원, 댓글/답글, WebSocket 알림, Runner 샌드박스 실행 로컬 통합 검증 완료 |
| 최종 보고서 PDF | 완료 | `docs/deliverables/report.pdf` 생성 및 PDF viewer 렌더링 확인 |

## 제안서 기준 정합성

제안서의 주제는 Docker 샌드박스 기반 실시간 알고리즘 코드 멘토링 플랫폼이다. 현재 초기 레포 문서는 아래 범위를 기준으로 맞춰져 있다.

- React + Monaco Editor 기반 코드 화면
- 라인별 질문/답변과 WebSocket 갱신 알림
- FastAPI API/WebSocket Server와 Runner Service 분리
- PostgreSQL에 세션, 코드 스냅샷, 질문/답변, 실행 로그 저장
- Runner가 요청마다 일회용 Docker 컨테이너를 생성해 Python 단일 파일 실행
- PostgreSQL 스키마는 Alembic 마이그레이션으로 관리
- 프론트엔드는 정적 build 산출물, 백엔드/Runner/PostgreSQL은 Azure VM의 Docker Compose 기준
- Redis Queue, Kubernetes, Auto Scaling, 실시간 공동 편집, 로그인/회원가입은 초기 구현 범위에서 제외

현재 구현은 로컬 Docker Compose 기준 통합 흐름과 Azure 공개 배포 흐름까지 검증했다. Azure VM backend stack, Caddy 기반 HTTPS/WSS reverse proxy, Azure Static Web Apps 프론트엔드 배포가 완료됐으며, 공개 URL 기준으로 세션 생성, 코드 실행, WebSocket 알림, 실행 이력/댓글 유지까지 확인했다.

## 초기 통합 순서

세 역할은 동시에 시작해도 되지만, PR 통합은 아래 순서를 우선한다.

| 순서 | 담당 | 먼저 끝낼 것 | 이유 |
| --- | --- | --- | --- |
| 1 | Backend | FastAPI app, health check, 세션 API skeleton | Cloud & Infra가 compose health check와 service port를 잡을 수 있음 |
| 2 | Backend + Runner | `POST /run` skeleton, 요청/응답 모델, timeout 필드 처리 | Frontend와 Cloud & Infra가 같은 Runner 계약을 보고 작업 가능 |
| 3 | Cloud & Infra | postgres/backend/runner compose 연결, network/env/health check | 로컬 통합 실행 기준 생성 |
| 4 | Frontend | Vite scaffold, Monaco 화면, 세션/실행 결과/질문 UI | Backend 준비 전에도 화면 작업 가능 |
| 5 | 전체 | 실제 API 연결, WebSocket 갱신, Docker Runner 실행 통합 | 최종 보고서와 데모 흐름 확인 가능 |

Frontend 초기 작업은 1~3번이 끝날 때까지 기다리지 않고 `docs/api-contract.md` 기준으로 진행했다. 최종 상태에서는 실제 backend API와 WebSocket 연결로 교체되어 있다.

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
| 로컬 compose 스모크 테스트 | 완료 | 빈 DB 기준 `python scripts/compose-smoke-test.py`로 backend/runner/postgres 흐름 검증 |
| Azure VM 배포 문서 | 완료 | `infra/azure-vm-deployment.md`에 배포 절차, 포트 정책, 검증 기준 정리 |
| Azure VM 배포 검증 | 완료 | Korea Central `cloudterm-vm`에서 compose 배포, 컨테이너 health, smoke test, 외부 `https://cloudterm-backend-3.koreacentral.cloudapp.azure.com/health` 응답 확인 |
| Azure Static Web Apps 공개 배포 | 완료 | GitHub Actions workflow로 프론트 정적 배포 완료 |
| Cloud/Infra 증거 문서 | 완료 | `infra/evidence.md`에 실제 검증 결과와 최종 데모 전 재검증 체크리스트 정리 |
| Frontend lint/build | 완료 | `npm run lint`, `npm run build` 통과 |
| Backend/Runner unit test | 완료 | backend 9개, runner 3개 단위 테스트 통과 |
| Browser 통합 검증 | 완료 | 공개 Static Web Apps URL에서 세션 생성, 정상 실행, WebSocket 이벤트, 실행 이력, 댓글 저장, 새로고침 유지 확인 |

## 역할별 최종 구현 상태

### Frontend

- Vite React TypeScript 기반 화면 구현 완료
- 세션 생성/입장, Monaco Editor, 실행 결과 패널 구현 완료
- 실제 backend REST API와 WebSocket 연동 완료
- 실행 이력 조회 및 코드 스냅샷 복원 UI 구현 완료
- 댓글/답글 작성과 WebSocket 이벤트 로그 구현 완료

### Backend

- 세션 생성/조회, 실행, 댓글/답글, WebSocket 알림, 실행 로그 저장 구현 완료
- 실행 이력 조회와 실행 당시 코드 스냅샷 반환 구현 완료
- Runner 내부 API 연동 및 runner 서비스 구현 완료
- Alembic 기반 DB 마이그레이션 적용 완료
- Runner 샌드박스 transient failure 재시도 추가

주의:

- API 계약 변경이 필요하면 구현 전에 `docs/api-contract.md`를 먼저 갱신한다.
- DB 마이그레이션은 Alembic으로 관리한다.

### Cloud & Infra

- Docker Compose backend/runner/postgres 통합 완료
- backend/runner Dockerfile 작성 완료
- Runner 컨테이너 제한(timeout, memory, CPU, network, read-only, non-root) 적용 완료
- Docker Compose host port binding을 `127.0.0.1`로 제한해 backend/runner/postgres 직접 외부 노출 축소
- Azure VM backend stack 배포 검증 완료
- Caddy 기반 HTTPS/WSS reverse proxy 구성 완료
- Azure Static Web Apps 프론트엔드 배포 workflow 구성 및 공개 E2E 검증 완료
- `.env.example`, Azure VM runbook, evidence 문서 정리 완료

## 온보딩 확인 항목

새 팀원이 레포를 받은 뒤 아래 항목을 확인하면 된다.

- 기준 브랜치는 `dev`다.
- 각자 역할에 맞는 `feat/...` 브랜치를 만든다.
- 작업 전 `README.md`, `docs/project-status.md`, `docs/api-contract.md`를 확인한다.
- 프론트 실제 연동 기준은 `docs/frontend-integration-guide.md`를 함께 확인한다.
- PostgreSQL 컨테이너 실행은 검증됐다.
- backend/runner/postgres compose 통합, Azure VM backend stack 배포 검증, frontend 실제 API/WebSocket 연동, Azure Static Web Apps 공개 배포 검증은 완료되었다.
- 실행 이력과 코드 스냅샷 복원까지 포함한 로컬 브라우저 통합 검증은 완료되었다.
- Cloud/Infra 배포 증거와 재검증 체크리스트는 `infra/evidence.md`를 확인한다.
- 현재 Azure VM은 공개 데모를 위해 실행 중일 수 있으며, 비용 절감을 위해 deallocate하면 backend/API/WebSocket/Runner/DB는 응답하지 않는다. Azure backend 실제 검증 전에는 VM 실행 상태와 health check를 확인한다.
- backend/runner의 로컬 compose 스모크 테스트는 `python scripts/compose-smoke-test.py`로 실행한다.
