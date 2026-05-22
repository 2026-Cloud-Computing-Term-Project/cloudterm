# Runner Sandbox Policy

Runner는 사용자가 보낸 Python 단일 파일 코드를 일회용 Docker 컨테이너에서 실행한다. 이 문서는 backend/runner skeleton이 나오기 전 Cloud & Infra가 먼저 고정할 제한 기준이다.

## 기본 원칙

- 브라우저는 Runner를 직접 호출하지 않는다. Backend만 `RUNNER_URL`로 Runner 내부 API를 호출한다.
- Runner service는 요청마다 별도 실행 컨테이너를 만들고, 실행 컨테이너는 한 번 실행 후 폐기한다.
- 실행 제한은 요청 값보다 인프라 기본값이 우선한다. 초기 기본 timeout은 `.env.example`의 `RUN_TIMEOUT_SECONDS`를 기준으로 한다.
- Python 단일 파일 실행만 초기 범위다. 여러 파일, 패키지 설치, 다른 언어는 이번 초기 통합 범위가 아니다.

## 제한 기준

| 항목 | 초기 기준 | 확정 전 확인 |
| --- | --- | --- |
| Timeout | `RUN_TIMEOUT_SECONDS`를 기본값과 상한으로 사용한다. 요청의 `timeout_seconds`가 더 크면 허용하지 않는다. | Backend와 Runner 중 어느 계층에서 거절할지 `POST /run` skeleton에서 확정한다. |
| Memory | 실행 컨테이너에 메모리 제한을 둔다. 초기 후보는 128 MB 수준이다. | Python 실행과 기본 입출력 처리에 충분한지 smoke test로 확인한다. |
| Network | 사용자 코드 실행 컨테이너는 외부 네트워크를 쓰지 않는다. | Docker 실행 옵션에서 `none` 네트워크가 적용되는지 확인한다. |
| Filesystem | 실행 컨테이너 root filesystem은 read-only를 목표로 한다. | Python 런타임이 필요한 임시 경로를 tmpfs로 분리해 검증한다. |
| Temp/workdir | 요청마다 격리된 작업 디렉터리를 사용하고, 코드 파일은 그 실행에만 보이게 한다. | host mount 방식과 container 내부 파일 생성 방식 중 구현이 단순한 쪽을 skeleton 이후 선택한다. |
| stdout/stderr/exit code | stdout, stderr, exit code, timed_out을 분리해서 반환한다. | timeout 시 exit code convention을 Runner 구현에서 테스트로 고정한다. |
| Cleanup | 실행 컨테이너와 임시 작업 디렉터리는 요청 종료 후 정리한다. | 정리 대상은 Runner가 만든 실행 단위로만 식별한다. |

## Docker 실행 옵션 초안

실제 코드는 runner skeleton이 생긴 뒤 작성한다. 현재 기준은 아래 옵션을 구현 후보로 둔다.

```text
--network none
--memory 128m
--memory-swap 128m
--read-only
--tmpfs /tmp:rw,nosuid,nodev,size=64m
--workdir /workspace
```

`--cpus` 또는 process count 제한은 Docker Engine 환경별 동작을 확인한 뒤 추가한다. Azure VM에서 Docker Engine 버전과 Compose plugin 버전을 확인하기 전까지 필수 조건으로 쓰지 않는다.

Runner service가 Docker daemon에 접근하는 방식은 별도 위험 검토가 필요하다. Docker socket을 컨테이너에 mount하면 Runner service가 host Docker를 강하게 제어할 수 있으므로, socket mount를 쓰더라도 외부 공개 금지, 내부 네트워크 제한, 실행 컨테이너 label 격리, 최소 권한 대안을 같이 검토한다.

## 실패 처리

- timeout은 `timed_out: true`로 드러낸다.
- 런타임 오류는 stderr와 non-zero exit code로 드러낸다.
- Runner 내부 오류와 사용자 코드 오류를 같은 실패로 섞지 않는다.
- Docker 실행 실패는 backend가 사용자 코드 결과로 오해하지 않도록 서버 오류로 처리한다.

## Skeleton 이후 검증할 것

- 정상 코드가 stdout과 exit code 0을 반환한다.
- 문법 오류가 stderr와 non-zero exit code를 반환한다.
- 무한 루프가 timeout으로 중단된다.
- 네트워크 접근 코드가 실패한다.
- 파일 쓰기는 허용된 임시 경로 안에서만 가능하다.
- 실행 후 다음 요청이 이전 요청의 파일을 볼 수 없다.
