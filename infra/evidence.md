# Cloud & Infra Evidence

이 문서는 Cloud & Infra 담당 산출물이 무엇을 구현했고, 어떤 범위까지 검증했는지 남기는 증거 문서다. 시크릿, SSH key 경로, 인증 코드, 개인 로컬 경로는 기록하지 않는다.

## 이번 Cloud & Infra 역할

이번 세션에서 수행한 역할은 Azure VM 위에 backend stack을 실제 배포하고, 제안서 기준 Cloud/Infra 실행 가능성을 검증한 것이다.

완료한 범위:

- Azure VM 기반 backend stack 배포
- `backend`, `runner`, `postgres` Docker Compose 실행
- 빈 PostgreSQL DB 기준 Alembic migration 적용
- Runner가 backend 내부 호출 경로로 동작하는지 검증
- backend 외부 공개와 runner/postgres 외부 비공개 포트 정책 검증
- 비용 절감을 위한 VM deallocate
- 프론트 실제 연동을 위한 backend endpoint, env, WebSocket 기준 정리

프론트/백엔드 담당 산출물과 함께 최종 확인된 범위:

- 프론트는 실제 REST API와 WebSocket으로 연결됨
- 실행 이력 조회와 코드 스냅샷 복원까지 로컬 브라우저 통합 검증됨
- Azure Static Web Apps 배포를 별도로 수행할 경우 HTTPS 환경에서 mixed content 발생 여부를 확인해야 함
- HTTPS 프론트에서 HTTP/WS backend 호출이 막히면 Cloud/Infra가 reverse proxy 또는 HTTPS/WSS 구성을 추가

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
| Public ports | `22`, `8000` |
| Private service ports | `8001`, `5432` |
| Current VM state | `PowerState/deallocated` |

Korea Central에서 `Standard_B2s`, `Standard_B2ms`, `Standard_B1ms`는 용량 제한으로 생성 실패했다. Korea South는 구독 정책으로 리소스 생성이 차단되어 `cloudterm-rg-ks` 리소스 그룹만 생성된 상태다. 삭제가 필요하면 대상 확인 후 별도 승인으로 처리한다.

## 배포 구성

Azure VM 내부 구성:

```text
Azure VM
  Docker Compose
    backend   -> public host port 8000
    runner    -> internal service port 8001
    postgres  -> internal service port 5432
```

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
| Backend external health | `http://52.231.65.10:8000/health` 응답 확인 |
| Runner external exposure | `8001` 외부 접근 차단 확인 |
| PostgreSQL external exposure | `5432` 외부 접근 차단 확인 |
| VM deallocate | `PowerState/deallocated` 확인 |
| Deallocate 후 endpoint | `http://52.231.65.10:8000/health` timeout 확인 |

Deallocate 후 backend endpoint가 응답하지 않는 것은 정상이다. 실제 Azure backend 검증이나 최종 데모 전에는 VM을 다시 시작하고 health check를 다시 확인한다.

## 최종 데모 전 재검증 체크리스트

1. `cloudterm-vm`을 시작한다.
2. VM 상태가 `PowerState/running`인지 확인한다.
3. VM에 접속해 repo 위치에서 `docker compose ps`를 확인한다.
4. 컨테이너가 내려가 있으면 `docker compose up --build -d`로 다시 올린다.
5. VM 내부에서 backend와 runner health를 확인한다.
6. VM 내부에서 `python3 scripts/compose-smoke-test.py`를 실행한다.
7. 외부 PC에서 `http://52.231.65.10:8000/health`를 확인한다.
8. 프론트 환경변수 `VITE_API_BASE_URL`, `VITE_WS_BASE_URL`이 현재 backend 주소를 가리키는지 확인한다.
9. 세션 생성, 코드 실행, 실행 이력, 코드 스냅샷 복원, 댓글/답글, WebSocket 알림을 브라우저에서 확인한다.
10. HTTPS 프론트 배포에서 mixed content가 발생하면 HTTPS/WSS reverse proxy 구성을 추가한다.

## 역할 완료 판단

Cloud & Infra 기준으로 완료된 것은 Azure VM backend stack 배포와 검증이다. 프로젝트 전체 기준 로컬 통합 검증은 프론트 실제 API/WebSocket 연동, 실행 이력, 코드 스냅샷 복원까지 완료됐다. Azure Static Web Apps와 HTTPS/WSS 검증은 별도 공개 배포를 선택할 때 필요한 운영 검증이다.
