from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request


def request_json(method: str, url: str, body: dict | None = None) -> dict:
    data = None
    headers = {}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        payload = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {url} failed: {exc.code} {payload}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"{method} {url} failed: {exc.reason}") from exc


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a compose smoke test against backend and runner.")
    parser.add_argument("--backend-base-url", default="http://localhost:8000")
    parser.add_argument("--runner-base-url", default="http://localhost:8001")
    args = parser.parse_args()

    print("Checking backend health...")
    backend_health = request_json("GET", f"{args.backend_base_url}/health")
    assert_true(backend_health.get("status") == "ok", "Backend health check failed")

    print("Checking runner health...")
    runner_health = request_json("GET", f"{args.runner_base_url}/health")
    assert_true(runner_health.get("status") == "ok", "Runner health check failed")

    print("Creating session...")
    session = request_json(
        "POST",
        f"{args.backend_base_url}/sessions",
        {"title": "compose smoke test"},
    )
    assert_true(session.get("session_id"), "Session creation failed")

    session_id = session["session_id"]

    print("Fetching session...")
    session_detail = request_json("GET", f"{args.backend_base_url}/sessions/{session_id}")
    assert_true(session_detail.get("session_id") == session_id, "Session lookup failed")

    print("Executing code...")
    run_result = request_json(
        "POST",
        f"{args.backend_base_url}/sessions/{session_id}/run",
        {
            "language": "python",
            "code": "print('hello from smoke test')",
            "stdin": "",
        },
    )
    assert_true(run_result.get("stdout") == "hello from smoke test\n", "Run stdout mismatch")
    assert_true(run_result.get("exit_code") == 0, "Run exit code mismatch")
    assert_true(not run_result.get("timed_out"), "Run timed out unexpectedly")

    print("Creating comment...")
    comment = request_json(
        "POST",
        f"{args.backend_base_url}/sessions/{session_id}/comments",
        {
            "line_number": 1,
            "body": "Why does this line print?",
            "author_name": "smoke-test",
        },
    )
    assert_true(comment.get("comment_id"), "Comment creation failed")

    print("Creating reply...")
    reply = request_json(
        "POST",
        f"{args.backend_base_url}/sessions/{session_id}/comments/{comment['comment_id']}/replies",
        {
            "body": "Because the runner executed it successfully.",
            "author_name": "backend",
        },
    )
    assert_true(reply.get("comment_id") == comment["comment_id"], "Reply creation failed")

    print("Listing comments...")
    comments = request_json("GET", f"{args.backend_base_url}/sessions/{session_id}/comments")
    assert_true(len(comments.get("comments", [])) >= 1, "Comment list is empty")

    print("Smoke test passed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc
