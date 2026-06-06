# Infra

클라우드와 로컬 실행 환경 담당 영역이다.

초기 책임:

- Docker Compose 구성
- PostgreSQL 서비스 구성
- Azure VM 배포 문서
- Nginx, 방화벽, 포트 정책
- 환경변수 관리
- Runner Docker 실행 제한

실제 시크릿은 `.env`에만 두고 Git에 올리지 않는다. 공개 기본값과 변수 이름은 `.env.example`에 기록한다.

## 첫 작업

```bash
git switch dev
git pull origin dev
git switch -c feat/cloud-compose-runner
docker compose config
docker compose up -d postgres
docker compose exec postgres pg_isready -U cloudterm -d cloudterm
docker compose ps
```

Docker 명령이 인식되지 않으면 먼저 Docker Desktop 설치와 PATH를 확인한다.

```powershell
winget install -e --id Docker.DockerDesktop
```

설치 직후에도 `docker` 명령이 안 잡히면 새 터미널을 열거나 Docker Desktop이 실행 중인지 확인한다.

초기 구현 순서:

1. backend/runner Dockerfile 작성 기준 결정
2. compose에 backend, runner 서비스 추가
3. backend와 runner health check 추가
4. Runner 컨테이너 실행 제한 문서화
5. Azure VM 배포 메모 작성

## 현재 Cloud/Infra 산출물

`infra/`에는 Azure 운영 문서가 있고, 실제 실행 구성은 repo 루트와 backend/runner 폴더에도 걸쳐 있다.

| 경로 | 역할 |
| --- | --- |
| `infra/azure-vm-deployment.md` | Azure VM 배포, 검증, 정지, 재시작 runbook |
| `infra/evidence.md` | 실제 Azure 배포 검증 결과와 Cloud/Infra 역할 완료 근거 |
| `docker-compose.yml` | backend/runner/postgres 로컬 및 VM compose 통합 |
| `.env.example` | 공개 환경변수 이름과 기본값 |
| `backend/Dockerfile` | backend 컨테이너 빌드 기준 |
| `runner/Dockerfile` | runner 컨테이너 빌드 기준 |
| `scripts/compose-smoke-test.py` | backend/runner/postgres 통합 smoke test |
| `docs/frontend-integration-guide.md` | 프론트 실제 API/WebSocket 연동 전달 문서 |

## 배포 문서

- Azure VM 배포 절차와 포트 정책은 `infra/azure-vm-deployment.md`를 기준으로 한다.
- 실제 배포 검증 증거와 역할 완료 판단은 `infra/evidence.md`를 기준으로 한다.
- 실제 Azure VM backend stack 배포 검증은 `cloudterm-rg`의 `cloudterm-vm`에서 완료됐다.
- 현재 검증된 backend health endpoint는 `https://cloudterm-backend-3.koreacentral.cloudapp.azure.com/health`다.
- 현재 검증된 frontend 공개 URL은 `https://yellow-field-0ad776800.7.azurestaticapps.net`다.
- frontend 배포 시 API/WebSocket 환경변수는 `infra/azure-vm-deployment.md`의 HTTPS/WSS 검증값을 기준으로 맞춘다.
- compose host port binding은 `127.0.0.1`로 제한해 backend/runner/postgres가 LAN 또는 public IP로 직접 노출되지 않게 한다.
- 비용 절감을 위해 VM이 deallocate 상태이면 backend/API/WebSocket/Runner/DB는 응답하지 않는다. 실제 Azure 검증 전 VM을 다시 시작한다.

주의:

- 최종 배포와 로컬 통합 검증은 빈 PostgreSQL volume 기준이다.
- 이전 backend 버전에서 `create_all`로 만든 테이블이 남아 있는 로컬 DB는 Alembic 초기 마이그레이션과 충돌할 수 있다.
- 기존 로컬 DB 데이터를 보존할 필요가 없을 때만 본인 환경에서 `docker compose down -v`로 PostgreSQL volume을 초기화한다. 이 명령은 로컬 PostgreSQL 데이터를 삭제한다.
- `.env.example` 변수 이름 변경은 팀 전체에 영향이 있으므로 먼저 공유한다.
- Azure VM이 실행 중이면 비용이 발생한다. 중지나 삭제는 대상 리소스를 확인한 뒤 별도 승인으로 진행한다.
