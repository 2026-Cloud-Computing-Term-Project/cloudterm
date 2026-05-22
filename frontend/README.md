# Frontend

프론트엔드 담당 영역이다.

초기 책임:

- 세션 생성/입장 화면
- Monaco Editor 기반 코드 작성 화면
- 실행 버튼과 결과 패널
- 라인별 질문/답변 UI
- `VITE_API_BASE_URL`, `VITE_WS_BASE_URL` 기반 API/WebSocket 연결

기능 구현 전 `docs/api-contract.md`의 endpoint와 WebSocket event 이름을 먼저 확인한다.

## 첫 작업

현재 `frontend/`에는 아직 `package.json`이 없다. 프론트엔드 담당자가 feature branch에서 Vite React scaffold를 생성하는 것이 첫 작업이다.

```bash
git switch dev
git pull origin dev
git switch -c feat/frontend-editor
cd frontend
npm create vite@latest . -- --template react-ts
npm install
```

Scaffold 이후 필요한 후보:

- `@monaco-editor/react`
- API client 구조
- WebSocket client 구조
- 세션 입장 화면
- 코드 작성/실행 결과 화면

`npm run dev`가 동작하는 상태가 되면 실행 방법을 이 파일과 루트 `README.md`에 같이 기록한다.
