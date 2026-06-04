# Azure VM Deployment Runbook

이 문서는 최종 제출용 Azure VM 배포 절차를 고정한다. 실제 시크릿은 `.env`에만 작성하고 Git에 올리지 않는다.

## 배포 기준

- Frontend: Azure Static Web Apps
- Backend stack: Azure VM 내부 Docker Compose
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
| Deployed services | `backend`, `runner`, `postgres` |

검증 결과:

- VM provisioning state와 power state 정상
- Docker Engine과 Docker Compose 설치 완료
- `docker compose up --build -d` 성공
- `backend`, `runner`, `postgres` 컨테이너 health 정상
- VM 내부에서 `python3 scripts/compose-smoke-test.py` 통과
- 외부 PC에서 `http://52.231.65.10:8000/health` 응답 확인
- 외부에서 `8001`, `5432` 포트 직접 접근 차단 확인

현재 운영 상태:

- 2026-06-04 배포 검증 후 비용 절감을 위해 `cloudterm-vm`을 deallocate 상태로 전환했다.
- VM이 deallocate 상태이면 `http://52.231.65.10:8000` backend endpoint는 응답하지 않는다.
- 실제 Azure backend 검증이나 최종 데모 전에는 `cloudterm-vm`을 다시 시작한 뒤 health check와 compose 상태를 재확인한다.

Korea Central에서 `Standard_B2s`, `Standard_B2ms`, `Standard_B1ms`는 현재 용량 제한으로 VM 생성이 실패했다. Korea South는 구독 정책으로 리소스 생성이 차단되어 `cloudterm-rg-ks` 리소스 그룹만 생성된 상태다. 이 리소스 그룹 정리는 비용·삭제 영향 확인 후 별도 승인으로 처리한다.

## VM 준비

권장 VM 조건:

- Ubuntu 22.04 LTS 또는 24.04 LTS
- 현재 검증 VM size는 `Standard_D2s_v3`
- Docker Engine과 Docker Compose plugin 설치
- inbound 공개 포트는 SSH와 backend API 포트만 허용

외부 공개 포트:

| Port | 용도 | 공개 여부 |
| --- | --- | --- |
| 22 | SSH 운영 접속 | 필요할 때만 허용 |
| 8000 | backend HTTP/WebSocket API | 공개 |
| 8001 | runner internal API | 비공개 |
| 5432 | PostgreSQL | 비공개 |

Runner와 PostgreSQL은 Docker Compose 내부 네트워크에서만 backend가 접근한다. 브라우저나 frontend가 runner/postgres를 직접 호출하지 않는다.

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
DATABASE_URL=postgresql://cloudterm:cloudterm@postgres:5432/cloudterm
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

실제 서비스용 DB 비밀번호를 바꾸면 `docker-compose.yml`의 `postgres.environment`와 `DATABASE_URL`을 같은 값으로 맞춘다.

서비스를 빌드하고 실행한다.

```bash
docker compose up --build -d
docker compose ps
```

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
curl http://<AZURE_VM_PUBLIC_IP>:8000/health
```

현재 검증된 backend health endpoint:

```bash
curl http://52.231.65.10:8000/health
```

Frontend 배포 환경변수:

```text
VITE_API_BASE_URL=http://<AZURE_VM_PUBLIC_IP>:8000
VITE_WS_BASE_URL=ws://<AZURE_VM_PUBLIC_IP>:8000
```

현재 검증된 Azure VM backend 주소를 사용할 경우:

```text
VITE_API_BASE_URL=http://52.231.65.10:8000
VITE_WS_BASE_URL=ws://52.231.65.10:8000
```

프론트엔드가 HTTPS로 배포되면 브라우저 mixed content 정책 때문에 HTTP/WebSocket 연결이 차단될 수 있다. 이 경우 backend 앞에 HTTPS reverse proxy를 두고 `VITE_API_BASE_URL`은 `https://...`, `VITE_WS_BASE_URL`은 `wss://...`로 맞춘다.

프론트엔드 실제 연동 순서와 WebSocket 처리 기준은 `docs/frontend-integration-guide.md`를 함께 본다.

## 운영 주의

- 최종 배포는 빈 PostgreSQL volume 기준이다.
- 기존 로컬 DB 데이터를 보존할 필요가 없을 때만 `docker compose down -v`를 사용한다.
- `docker compose down -v`는 PostgreSQL volume을 삭제한다.
- runner 컨테이너는 host Docker daemon 접근을 위해 `/var/run/docker.sock`을 mount한다.
- runner/postgres 포트는 Azure Network Security Group에서 열지 않는다.
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
- `http://52.231.65.10:8000` backend endpoint는 응답하지 않는다.
- 디스크와 Standard Public IP 같은 고정 리소스 비용은 남을 수 있다.
- VM을 다시 시작하면 repo와 Docker Compose 배포 상태는 디스크에 남아 있다.
- 프론트엔드는 VM 정지 중에도 mock 데이터나 로컬 backend 기준으로 작업할 수 있다.

## 완료 기준

- Azure VM에서 `docker compose up --build -d` 성공
- `backend`, `runner`, `postgres` health 정상
- `python scripts/compose-smoke-test.py` 통과
- 외부 PC에서 `http://<AZURE_VM_PUBLIC_IP>:8000/health` 응답 확인
- runner/postgres 포트가 외부에서 직접 열려 있지 않음
- Frontend의 API/WebSocket 환경변수가 Azure VM backend 주소를 가리킴
