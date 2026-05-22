# Azure VM Deployment Notes

이 문서는 실제 배포 절차가 아니라 Azure VM 배포 전 확인할 운영 메모 초안이다. frontend는 Azure Static Web Apps, backend/runner/postgres는 Azure VM의 Docker Compose 기준으로 둔다.

## 구성 요소

- Azure VM: Docker Engine과 Compose plugin 실행용 Linux VM
- Docker Compose: backend, runner, postgres 실행
- PostgreSQL volume: VM 로컬 Docker volume로 시작
- Nginx: 외부 HTTPS 요청을 backend로 reverse proxy
- Azure Network Security Group: 공개 포트 제한
- Firewall: VM 내부 방화벽이 켜져 있으면 Nginx 포트만 공개

## 포트 기준

| 대상 | 포트 | 공개 여부 | 비고 |
| --- | --- | --- | --- |
| SSH | 22 | 제한 공개 | 관리자 IP로 제한하는 것이 좋다. |
| HTTP | 80 | 공개 | HTTPS 발급 또는 redirect용이다. |
| HTTPS | 443 | 공개 | 브라우저가 접근하는 backend API 진입점이다. |
| Backend | 8000 | 비공개 | Nginx 뒤 내부 포트로 둔다. |
| Runner | 8001 | 비공개 | Backend만 Compose network에서 호출한다. |
| PostgreSQL | 5432 | 비공개 | 외부 공개하지 않는다. |

## Compose 운영 기준

- VM에는 repo를 clone하고 배포 대상 브랜치 또는 태그를 checkout한다.
- 실제 시크릿은 `.env`에 두고 Git에 올리지 않는다.
- `.env.example`의 변수 이름은 배포 환경에서도 유지한다.
- backend/runner Dockerfile과 health check가 생긴 뒤 `docker compose up --build -d`를 배포 기준 명령으로 둔다.
- 배포 후 `docker compose ps`, backend health check, Runner health check, PostgreSQL readiness를 확인한다.

## Nginx TODO

- API base path 또는 subdomain 결정
- WebSocket proxy 설정
- request body size 제한
- timeout 설정
- HTTPS 인증서 발급 방식 결정
- frontend Static Web Apps의 CORS origin 확정

## Firewall TODO

- NSG inbound rule에서 80/443만 공개
- SSH는 관리자 IP로 제한
- 8000, 8001, 5432는 외부 공개 금지
- VM 내부 firewall 사용 여부 결정

## 데이터와 복구

- PostgreSQL named volume은 VM 로컬 상태이므로 데모 전 백업 방법을 정한다.
- volume 삭제 명령은 운영 절차에 넣지 않는다.
- schema 변경은 backend 마이그레이션 도구가 정해진 뒤 그 도구를 기준으로 한다.

## 아직 기다려야 하는 것

- backend app entrypoint와 health check endpoint
- runner app entrypoint, health check endpoint, `POST /run` skeleton
- backend/runner Dockerfile
- Nginx가 proxy할 backend path와 WebSocket path
- 배포용 환경변수 실제 값
