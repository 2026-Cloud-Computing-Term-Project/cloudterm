# Frontend

This is the frontend for the Cloudterm project.

Cloudterm is a Docker sandbox based real-time algorithm code mentoring platform. This frontend provides the first mock UI for code mentoring sessions.

## Current Features

- Vite React TypeScript scaffold
- Monaco Editor based Python code editor
- Mock code execution result panel
- Mock line-based question and reply UI
- Mock WebSocket event log

## Run Locally

```bash
npm install
npm run dev
```

## Local URL:

- http://localhost:5173/

## Environment Variables

The frontend will use these environment variables when the real backend is connected later:

- VITE_API_BASE_URL=http://localhost:8000
- VITE_WS_BASE_URL=ws://localhost:8000

## Current Development Status

The current screen uses mock data based on docs/api-contract.md.

Later, the mock data will be replaced with real API calls:

- POST /sessions
- GET /sessions/{session_id}
- POST /sessions/{session_id}/run
- GET /sessions/{session_id}/comments
- POST /sessions/{session_id}/comments
- POST /sessions/{session_id}/comments/{comment_id}/replies
- WS /ws/sessions/{session_id}

## Notes

This frontend does not connect to the real backend yet. It is prepared first so frontend and backend can be developed in parallel.