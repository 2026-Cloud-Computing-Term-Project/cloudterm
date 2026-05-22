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

주의:

- `docker compose down -v`는 PostgreSQL volume을 제거할 수 있으므로 사용하지 않는다.
- `.env.example` 변수 이름 변경은 팀 전체에 영향이 있으므로 먼저 공유한다.
