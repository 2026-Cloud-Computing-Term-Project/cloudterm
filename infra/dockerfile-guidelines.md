# Backend and Runner Dockerfile Guidelines

backend/runner app entrypoint가 아직 없으므로 이 문서는 Dockerfile 구현 전 기준만 고정한다. 실제 Dockerfile은 각 service의 import path, health check, 실행 명령이 생긴 뒤 작성한다.

## 공통 기준

- Python slim 계열 이미지를 기본 후보로 둔다.
- service별 `requirements.txt`를 먼저 설치하고, app source는 그 뒤 copy해 dependency layer cache를 살린다.
- 컨테이너 실행 사용자는 root가 아니어야 한다.
- `.env` 파일은 이미지에 copy하지 않는다. 런타임 환경변수는 Compose 또는 배포 환경에서 주입한다.
- service port는 문서화된 계약을 따른다. Backend는 `8000`, Runner는 `8001`을 기준으로 한다.
- health check endpoint가 생기기 전에는 compose service health check를 확정하지 않는다.
- build context와 Dockerfile 위치는 compose 통합 시 한 번에 맞춘다.

## Backend Dockerfile 기준

Backend Dockerfile은 FastAPI app entrypoint가 생긴 뒤 작성한다.

예상 기준:

- `backend/requirements.txt` 설치
- `DATABASE_URL`, `RUNNER_URL`, `RUN_TIMEOUT_SECONDS`를 런타임 환경변수로 사용
- `uvicorn`으로 app을 `0.0.0.0:8000`에 바인딩
- `/health`가 생긴 뒤 compose health check 추가
- DB 마이그레이션 도구가 정해지면 schema 변경은 그 도구를 기준으로 한다

아직 확정하지 않을 것:

- app module path
- migration command
- production worker count
- reverse proxy header 설정

## Runner Dockerfile 기준

Runner Dockerfile은 `POST /run` skeleton과 health check가 생긴 뒤 작성한다.

예상 기준:

- `runner/requirements.txt` 설치
- `RUN_TIMEOUT_SECONDS`를 런타임 환경변수로 사용
- `uvicorn`으로 app을 `0.0.0.0:8001`에 바인딩
- `/health`가 생긴 뒤 compose health check 추가
- 사용자 코드 실행 컨테이너를 만들기 위한 Docker 접근 방식은 별도 검토 후 확정

아직 확정하지 않을 것:

- Runner app module path
- Docker socket mount 여부와 권한 축소 방식
- 실행 컨테이너 이미지 이름
- stdout/stderr size limit

## Compose 통합 전 체크리스트

- Backend와 Runner 모두 app entrypoint가 있다.
- Backend와 Runner 모두 health check endpoint가 있다.
- Runner `POST /run` 요청/응답 모델이 `docs/api-contract.md`와 맞다.
- `.env.example`의 변수 이름만으로 로컬 compose 실행이 가능하다.
- backend가 `http://runner:8001`로 Runner를 호출할 수 있다.
- PostgreSQL service 이름은 `postgres`로 유지된다.
