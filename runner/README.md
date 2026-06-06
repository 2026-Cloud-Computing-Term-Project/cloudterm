# Runner

사용자 코드를 격리 실행하는 Runner service 영역이다.

초기 책임:

- `POST /run` 내부 API 제공
- Python 단일 파일 실행
- stdout/stderr/exit code/timed_out 반환
- timeout 적용
- Docker 실행 제한 적용 준비

Runner API 요청/응답 형식은 `docs/api-contract.md`를 기준으로 한다. Docker 샌드박스 옵션과 배포 제한은 Cloud & Infra 담당 영역과 같이 맞춘다.

현재 구현 범위:

- `GET /health`
- `POST /run`
- Python 단일 파일을 Docker 샌드박스에서 실행
- stdout/stderr/exit code/timed_out 반환
- 요청별 타임아웃 처리
- 네트워크 차단, read-only rootfs, non-root user, CPU/memory/pids 제한 적용

주의:

- runner 컨테이너는 Docker 데몬에 접근해야 하므로 `docker.sock` 마운트가 필요하다.
- runner API는 Docker daemon 접근 권한을 간접적으로 가지므로 public internet에 직접 노출하지 않는다. compose host port는 로컬 debug용 `127.0.0.1` binding만 허용한다.
- 샌드박스 이미지는 기본값으로 `python:3.12-slim`을 사용한다.
- 샌드박스 제한값은 `RUNNER_SANDBOX_*` 환경변수로 조정할 수 있다.

## 첫 작업

```bash
git switch dev
git pull origin dev
git switch -c feat/backend-runner-api
cd runner
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

`feat/backend-runner-api`는 Backend 담당자가 Runner API를 별도 PR로 분리할 때 쓰는 브랜치다. Backend 첫 PR에 포함할지 별도 PR로 나눌지는 작업 크기를 보고 정한다.

초기 구현 순서:

1. FastAPI app scaffold
2. health check endpoint
3. `POST /run`
4. Python 단일 파일 실행
5. timeout 처리
6. stdout/stderr/exit code/timed_out 응답 고정

`requirements.txt`는 시작용 의존성 목록이다. Docker 실행 제한은 Cloud & Infra 담당 작업과 맞춰서 확정한다.
