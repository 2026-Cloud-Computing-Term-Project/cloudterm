# Cloud & Infra Evidence

이 문서는 Cloud & Infra 담당 산출물이 무엇을 구현했고, 어떤 범위까지 검증했는지 남기는 증거 문서다. 시크릿, SSH key 경로, 인증 코드, 개인 로컬 경로는 기록하지 않는다.

## 이번 Cloud & Infra 역할

이번 세션에서 수행한 역할은 Azure VM 위에 backend stack을 실제 배포하고, Azure Static Web Apps 프론트엔드와 HTTPS/WSS backend 공개 연동까지 검증한 것이다.

완료한 범위:

- Azure VM 기반 backend stack 배포
- `backend`, `runner`, `postgres` Docker Compose 실행
- 빈 PostgreSQL DB 기준 Alembic migration 적용
- Runner가 backend 내부 호출 경로로 동작하는지 검증
- backend 외부 공개와 runner/postgres 외부 비공개 포트 정책 검증
- Caddy 기반 HTTPS/WSS reverse proxy 구성
- Azure Static Web Apps 배포 workflow 구성
- 공개 URL 기준 브라우저 E2E 검증
- 프론트 실제 연동을 위한 backend endpoint, env, WebSocket 기준 정리

프론트/백엔드 담당 산출물과 함께 최종 확인된 범위:

- 프론트는 실제 REST API와 WebSocket으로 연결됨
- 실행 이력 조회와 코드 스냅샷 복원까지 로컬 브라우저 통합 검증됨
- Azure Static Web Apps 공개 배포에서 HTTPS/WSS backend 연동 검증됨
- 공개 URL에서 세션 생성, 코드 실행, WebSocket 이벤트, 실행 이력/댓글 유지 검증됨

## Azure 리소스

| 항목 | 값 |
| --- | --- |
| Subscription type | Azure for Students |
| Resource group | `cloudterm-rg` |
| Region | Korea Central |
| VM | `cloudterm-vm` |
| VM size | `Standard_D2s_v3` |
| OS | Ubuntu 22.04 LTS |
| Public IP | `52.231.65.10` |
| Backend FQDN | `cloudterm-backend-3.koreacentral.cloudapp.azure.com` |
| Static Web Apps URL | `https://yellow-field-0ad776800.7.azurestaticapps.net` |
| Backend `FRONTEND_BASE_URL` | `https://yellow-field-0ad776800.7.azurestaticapps.net` |
| Public ports | `22`, `80`, `443` |
| Local-only service ports | `127.0.0.1:8000`, `127.0.0.1:8001`, `127.0.0.1:5432` |
| Current VM state | `PowerState/running` |

Korea Central에서 `Standard_B2s`, `Standard_B2ms`, `Standard_B1ms`는 용량 제한으로 생성 실패했다. Korea South는 구독 정책으로 리소스 생성이 차단되어 `cloudterm-rg-ks` 리소스 그룹만 생성된 상태다. 삭제가 필요하면 대상 확인 후 별도 승인으로 처리한다.

## 배포 구성

Azure 공개 배포 구성:

```text
Browser
  -> Azure Static Web Apps
  -> HTTPS/WSS cloudterm-backend-3.koreacentral.cloudapp.azure.com
  -> Azure VM Caddy reverse proxy
  Docker Compose
    backend   -> service port 8000, host-local 127.0.0.1:8000
    runner    -> service port 8001, host-local 127.0.0.1:8001
    postgres  -> service port 5432, host-local 127.0.0.1:5432
```

공개 데모는 HTTPS/WSS endpoint를 기준으로 진행한다. backend direct HTTP, runner, PostgreSQL host port는 외부 공개 대상이 아니다.

관련 repo 산출물:

| 경로 | 역할 |
| --- | --- |
| `docker-compose.yml` | backend/runner/postgres compose 통합 |
| `.env.example` | 공개 환경변수 이름과 기본값 |
| `backend/Dockerfile` | backend 컨테이너 빌드 기준 |
| `runner/Dockerfile` | runner 컨테이너 빌드 기준 |
| `scripts/compose-smoke-test.py` | 세션 생성, 실행, 댓글 흐름 smoke test |
| `infra/azure-vm-deployment.md` | Azure VM 배포/정지/재시작 runbook |
| `docs/frontend-integration-guide.md` | 프론트 실제 API/WebSocket 연동 기준 |
| `.github/workflows/azure-static-web-apps-cloudterm-frontend.yml` | Azure Static Web Apps 배포 workflow |

## 검증 결과

| 검증 | 결과 |
| --- | --- |
| VM provisioning | `ProvisioningState/succeeded` |
| VM 실행 상태 | 배포 검증 당시 `PowerState/running` |
| Docker 설치 | Docker Engine과 Docker Compose 사용 가능 |
| Compose 배포 | `docker compose up --build -d` 성공 |
| Container health | `backend`, `runner`, `postgres` healthy |
| Backend internal health | `curl http://127.0.0.1:8000/health` 응답 |
| Runner internal health | `curl http://127.0.0.1:8001/health` 응답 |
| Smoke test | `python3 scripts/compose-smoke-test.py` 통과 |
| Frontend local integration | 세션 생성, 코드 실행, 실행 이력, 코드 스냅샷 복원, 댓글/답글, WebSocket 알림 확인 |
| Backend external HTTPS health | `https://cloudterm-backend-3.koreacentral.cloudapp.azure.com/health` 응답 확인 |
| Static Web Apps deploy | GitHub Actions workflow 성공 |
| Public browser E2E | `https://yellow-field-0ad776800.7.azurestaticapps.net`에서 세션 생성, 실행, WebSocket 이벤트, 실행 이력/댓글 유지 확인 |
| Backend direct HTTP exposure | `Allow-Backend-8000` NSG rule 삭제 후 public IP TCP `8000` timeout 확인 |
| Runner external exposure | `8001` 외부 접근 차단 확인 |
| PostgreSQL external exposure | `5432` 외부 접근 차단 확인 |
| DB persistence | Azure VM Docker volume 기준 세션/실행/댓글/답글 저장 확인 |

VM을 deallocate하면 backend endpoint가 응답하지 않는 것은 정상이다. 실제 Azure backend 검증이나 최종 데모 전에는 VM을 실행 상태로 두고 health check를 다시 확인한다.

## 최종 데모 전 재검증 체크리스트

1. `cloudterm-vm` 상태가 `PowerState/running`인지 확인한다.
2. VM이 deallocate 상태이면 시작한다.
3. VM에 접속해 repo 위치에서 `docker compose ps`를 확인한다.
4. 컨테이너가 내려가 있으면 `docker compose up --build -d`로 다시 올린다.
5. VM 내부에서 backend와 runner health를 확인한다.
6. VM 내부에서 `python3 scripts/compose-smoke-test.py`를 실행한다.
7. 외부 PC에서 `https://cloudterm-backend-3.koreacentral.cloudapp.azure.com/health`를 확인한다.
8. Static Web Apps workflow의 `VITE_API_BASE_URL`, `VITE_WS_BASE_URL`이 HTTPS/WSS backend 주소를 가리키는지 확인한다.
9. `https://yellow-field-0ad776800.7.azurestaticapps.net`에서 세션 생성, 코드 실행, 실행 이력, 코드 스냅샷 복원, 댓글/답글, WebSocket 알림을 브라우저에서 확인한다.
10. 공개 데모 후에는 비용 절감을 위해 VM deallocate 여부를 별도로 결정한다.

## 역할 완료 판단

Cloud & Infra 기준으로 완료된 것은 Azure VM backend stack 배포, Caddy HTTPS/WSS reverse proxy, Azure Static Web Apps 공개 배포 workflow, 공개 URL 기준 E2E 검증이다. 프로젝트 전체 기준으로 프론트 실제 API/WebSocket 연동, 실행 이력, 코드 스냅샷 복원, 댓글/답글 저장과 WebSocket 알림까지 확인됐다.
