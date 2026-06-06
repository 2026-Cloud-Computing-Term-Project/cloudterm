# Azure VM Deployment Runbook

이 문서는 최종 제출용 Azure VM 배포 절차를 고정한다. 실제 시크릿은 `.env`에만 작성하고 Git에 올리지 않는다.

## 배포 기준

- Frontend: Azure Static Web Apps
- Backend stack: Azure VM 내부 Docker Compose
- Public backend: Caddy reverse proxy를 통한 HTTPS/WSS
- VM services: `backend`, `runner`, `postgres`
- Sandbox: Runner가 요청마다 Docker sandbox container를 생성하고 실행 후 삭제
- DB 기준: 빈 PostgreSQL volume에서 Alembic migration 적용

## 현재 검증된 Azure 배포

2026-06-04 기준으로 아래 Azure VM 배포를 검증했다.

| 항목 | 값 |
| --- | --- |
| Subscription | Azure for Students |
| Resource group | `cloudterm-rg` |
| Region | Korea Central |
| VM | `cloudterm-vm` |
| VM size | `Standard_D2s_v3` |
| Public IP | `52.231.65.10` |
| OS | Ubuntu 22.04 LTS |
| Deployed services | `backend`, `runner`, `postgres`, `cloudterm-caddy` |
| Backend HTTPS endpoint | `https://cloudterm-backend-3.koreacentral.cloudapp.azure.com` |
| Frontend public URL | `https://yellow-field-0ad776800.7.azurestaticapps.net` |

검증 결과:

- VM provisioning state와 power state 정상
- Docker Engine과 Docker Compose 설치 완료
- `docker compose up --build -d` 성공
- `backend`, `runner`, `postgres` 컨테이너 health 정상
- VM 내부에서 `python3 scripts/compose-smoke-test.py` 통과
- 외부 PC에서 `https://cloudterm-backend-3.koreacentral.cloudapp.azure.com/health` 응답 확인
- Azure Static Web Apps 공개 URL에서 HTTPS/WSS backend 연동 확인
- 외부에서 `8000`, `8001`, `5432` 포트 직접 접근 차단 기준으로 정리
- `Allow-Backend-8000` NSG rule 삭제 후 public IP TCP `8000` 직접 접근 timeout 확인

현재 운영 상태:

- `cloudterm-vm`은 공개 데모 검증을 위해 실행 상태로 둘 수 있다.
- VM이 deallocate 상태이면 HTTPS/WSS backend endpoint와 Docker Compose 서비스는 응답하지 않는다.
- 실제 Azure backend 검증이나 최종 데모 전에는 `cloudterm-vm` 실행 상태, Caddy 상태, compose 상태, health check를 재확인한다.

Korea Central에서 `Standard_B2s`, `Standard_B2ms`, `Standard_B1ms`는 현재 용량 제한으로 VM 생성이 실패했다. Korea South는 구독 정책으로 리소스 생성이 차단되어 `cloudterm-rg-ks` 리소스 그룹만 생성된 상태다. 이 리소스 그룹 정리는 비용·삭제 영향 확인 후 별도 승인으로 처리한다.

## VM 준비

권장 VM 조건:

- Ubuntu 22.04 LTS 또는 24.04 LTS
- 현재 검증 VM size는 `Standard_D2s_v3`
- Docker Engine과 Docker Compose plugin 설치
- inbound 공개 포트는 SSH, HTTP 인증서 발급용 80, HTTPS/WSS용 443을 기준으로 허용

외부 공개 포트:

| Port | 용도 | 공개 여부 |
| --- | --- | --- |
| 22 | SSH 운영 접속 | 필요할 때만 허용 |
| 80 | Caddy ACME HTTP challenge / HTTP to HTTPS 처리 | 공개 |
| 443 | backend HTTPS/WSS reverse proxy | 공개 |
| 8000 | backend HTTP/WebSocket local debug | 비공개, `127.0.0.1` binding |
| 8001 | runner internal/local debug API | 비공개, `127.0.0.1` binding |
| 5432 | PostgreSQL local debug | 비공개, `127.0.0.1` binding |

Runner와 PostgreSQL은 Docker Compose 내부 네트워크에서만 backend가 접근한다. 브라우저나 frontend가 runner/postgres를 직접 호출하지 않는다. 공개 프론트엔드는 `443`의 HTTPS/WSS backend endpoint를 호출한다. `8000`, `8001`, `5432` compose host binding은 VM 또는 로컬 PC 안에서만 쓰는 debug 경로다.

## 배포 절차

VM에 접속한 뒤 repo를 준비한다.

```bash
git clone https://github.com/2026-Cloud-Computing-Term-Project/cloudterm.git
cd cloudterm
git switch dev
```

환경변수 파일을 만든다.

```bash
cp .env.example .env
```

VM 배포 기본값:

```text
POSTGRES_PASSWORD=<vm-local-db-password>
DATABASE_URL=postgresql://cloudterm:<vm-local-db-password>@postgres:5432/cloudterm
FRONTEND_BASE_URL=https://yellow-field-0ad776800.7.azurestaticapps.net
RUNNER_URL=http://runner:8001
RUN_TIMEOUT_SECONDS=3
RUNNER_SANDBOX_IMAGE=python:3.12-slim
RUNNER_SANDBOX_WORKDIR=/workspace
RUNNER_SANDBOX_MEMORY_LIMIT=128m
RUNNER_SANDBOX_CPU_NANO=500000000
RUNNER_SANDBOX_PIDS_LIMIT=64
RUNNER_SANDBOX_TMPFS_SIZE=64m
RUNNER_SANDBOX_USER=1000:1000
```

`<vm-local-db-password>`는 VM의 실제 `.env`에만 기록하고 Git에 올리지 않는다. `POSTGRES_PASSWORD`와 `DATABASE_URL`의 비밀번호 값은 반드시 같은 값으로 맞춘다.

서비스를 빌드하고 실행한다.

```bash
docker compose up --build -d
docker compose ps
```

HTTPS/WSS reverse proxy는 Caddy 컨테이너로 둔다. `backend` compose service에 접근하려면 Caddy를 compose network에 붙인다.

```bash
docker run -d \
  --name cloudterm-caddy \
  --restart unless-stopped \
  --network cloudterm_default \
  -p 80:80 \
  -p 443:443 \
  -v caddy_data:/data \
  -v caddy_config:/config \
  caddy:2 \
  caddy reverse-proxy \
  --from cloudterm-backend-3.koreacentral.cloudapp.azure.com \
  --to http://backend:8000
```

이미 `cloudterm-caddy` 컨테이너가 있으면 새로 만들지 말고 `docker ps`와 container logs로 상태를 확인한다.

## 검증

backend와 runner health check:

```bash
curl http://localhost:8000/health
curl http://localhost:8001/health
```

통합 smoke test:

```bash
python scripts/compose-smoke-test.py
```

외부 PC에서 backend 접근:

```bash
curl https://cloudterm-backend-3.koreacentral.cloudapp.azure.com/health
```

현재 검증된 backend health endpoint:

```bash
curl https://cloudterm-backend-3.koreacentral.cloudapp.azure.com/health
```

Frontend 배포 환경변수:

```text
VITE_API_BASE_URL=https://cloudterm-backend-3.koreacentral.cloudapp.azure.com
VITE_WS_BASE_URL=wss://cloudterm-backend-3.koreacentral.cloudapp.azure.com
```

Azure Static Web Apps workflow는 위 값을 build 환경변수로 주입한다.

VM 내부에서 직접 HTTP 검증이 필요할 때만 아래 host-local endpoint를 사용할 수 있다.

```text
http://127.0.0.1:8000/health
```

HTTPS 프론트엔드에서 HTTP/WS backend를 직접 호출하면 브라우저 mixed content 정책 때문에 차단된다. 공개 배포는 반드시 HTTPS/WSS backend endpoint를 기준으로 검증한다.

프론트엔드 실제 연동 순서와 WebSocket 처리 기준은 `docs/frontend-integration-guide.md`를 함께 본다.

## 운영 주의

- 최종 배포는 빈 PostgreSQL volume 기준이다.
- 기존 로컬 DB 데이터를 보존할 필요가 없을 때만 `docker compose down -v`를 사용한다.
- `docker compose down -v`는 PostgreSQL volume을 삭제한다.
- runner 컨테이너는 host Docker daemon 접근을 위해 `/var/run/docker.sock`을 mount한다.
- runner/postgres 포트는 Azure Network Security Group에서 열지 않는다.
- 공개 프론트엔드의 API/WebSocket 호출은 Caddy HTTPS/WSS reverse proxy를 기준으로 한다.
- `8000` 직접 공개는 사용하지 않는다. 예전 검증용 NSG rule이 남아 있으면 닫는다.
- sandbox 제한은 Runner 코드의 Docker SDK 옵션과 `.env.example`의 `RUNNER_SANDBOX_*` 값이 함께 SSoT다.
- 현재 Azure VM은 실행 중이면 비용이 발생한다. 중지나 삭제는 대상 리소스 확인 후 별도 승인으로 진행한다.

## 비용 절감용 VM 정지

제출 데모나 실제 Azure backend 검증을 하지 않는 시간에는 `cloudterm-vm`을 Stop 또는 deallocate 상태로 둔다.

정지 대상:

- Resource group: `cloudterm-rg`
- VM: `cloudterm-vm`
- Public IP: `52.231.65.10`

정지 영향:

- VM compute 비용은 중단된다.
- `https://cloudterm-backend-3.koreacentral.cloudapp.azure.com` backend endpoint는 응답하지 않는다.
- Static Web Apps 프론트엔드 자체는 계속 열릴 수 있지만 세션 생성, 코드 실행, WebSocket 기능은 실패한다.
- 디스크와 Standard Public IP 같은 고정 리소스 비용은 남을 수 있다.
- VM을 다시 시작하면 repo와 Docker Compose 배포 상태는 디스크에 남아 있다.
- 프론트엔드는 VM 정지 중에도 로컬 backend 기준으로 실행과 통합 검증을 진행할 수 있다.

## 완료 기준

- Azure VM에서 `docker compose up --build -d` 성공
- `backend`, `runner`, `postgres`, `cloudterm-caddy` 상태 정상
- `python scripts/compose-smoke-test.py` 통과
- 외부 PC에서 `https://cloudterm-backend-3.koreacentral.cloudapp.azure.com/health` 응답 확인
- `8000`, `8001`, `5432`이 외부에서 직접 열려 있지 않음
- Frontend의 API/WebSocket 환경변수가 HTTPS/WSS backend 주소를 가리킴
- Azure Static Web Apps 공개 URL에서 세션 생성, 코드 실행, WebSocket 이벤트, 실행 이력/댓글 유지 확인
