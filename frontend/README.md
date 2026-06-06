# Frontend

This is the frontend for the Cloudterm / CodeSession project.

The frontend is built with Vite, React, TypeScript, and Monaco Editor. It connects to the backend REST API and WebSocket API for session creation, code execution, comments, replies, and realtime event updates.

## Current Features

- Session creation and session joining
- `/sessions/{session_id}` link-based session access
- Copyable session link
- Monaco Editor based Python code editor
- Backend-connected code execution
- stdout / stderr / exit code / timeout result display
- Line-based comments and replies
- WebSocket event log
- Toast notifications
- Success / error / timeout demo buttons
- Local Vite proxy support for API and WebSocket calls

## Run Locally

Install dependencies:

```bash
npm install
```

Start the frontend dev server:

```bash
npm run dev
```

Local frontend URL:

```text
http://localhost:5173/
```

## Backend Connection

For local development, the frontend uses a Vite proxy.

Default frontend API settings:

```text
VITE_API_BASE_URL=/api
VITE_WS_BASE_URL=ws://localhost:5173
```

The Vite dev server proxies:

```text
/api -> http://localhost:8000
/ws  -> ws://localhost:8000
```

So the backend stack should be running first from the project root:

```bash
docker compose up --build
```

Backend health check:

```text
http://localhost:8000/health
```

## Production / Azure Backend

When connecting directly to the Azure VM backend, environment variables can be changed to:

```text
VITE_API_BASE_URL=http://52.231.65.10:8000
VITE_WS_BASE_URL=ws://52.231.65.10:8000
```

If the frontend is deployed over HTTPS, the backend should also support HTTPS/WSS to avoid browser mixed-content blocking.

## Notes

This frontend no longer uses mock data for the main session flow. It is connected to the backend API for session creation, code execution, comments, replies, and WebSocket event notifications.
