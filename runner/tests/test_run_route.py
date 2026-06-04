import unittest
import sys
from pathlib import Path
from unittest.mock import patch

from docker.errors import ImageNotFound

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.api.routes.run import _execute_python_in_docker


class FakeContainer:
    def __init__(self, kwargs: dict) -> None:
        self.kwargs = kwargs
        self.status = "created"
        self.id = "fake-container"
        self.attrs = {"State": {"ExitCode": 0}}
        self.removed = False

    def start(self) -> None:
        volumes = self.kwargs["volumes"]
        output_host_dir = next(
            Path(host_path)
            for host_path, mount in volumes.items()
            if mount["bind"] == "/workspace/output"
        )
        output_host_dir.joinpath("stdout.txt").write_text("hello\n", encoding="utf-8")
        output_host_dir.joinpath("stderr.txt").write_text("", encoding="utf-8")
        self.status = "exited"

    def reload(self) -> None:
        return None

    def kill(self) -> None:
        self.status = "exited"
        self.attrs["State"]["ExitCode"] = 124

    def remove(self, force: bool = False) -> None:
        self.removed = True


class FakeImages:
    def __init__(self, should_raise_not_found: bool = False) -> None:
        self.should_raise_not_found = should_raise_not_found
        self.pulled = False

    def get(self, image: str) -> None:
        if self.should_raise_not_found:
            raise ImageNotFound("missing")

    def pull(self, image: str) -> None:
        self.pulled = True


class FakeContainers:
    def __init__(self) -> None:
        self.created_kwargs: dict | None = None
        self.container: FakeContainer | None = None

    def create(self, **kwargs) -> FakeContainer:
        self.created_kwargs = kwargs
        self.container = FakeContainer(kwargs)
        return self.container


class FakeDockerClient:
    def __init__(self, should_raise_not_found: bool = False) -> None:
        self.images = FakeImages(should_raise_not_found=should_raise_not_found)
        self.containers = FakeContainers()


class RunnerSandboxRouteTestCase(unittest.TestCase):
    def test_execute_python_in_docker_returns_stdout_and_exit_code(self) -> None:
        fake_client = FakeDockerClient()

        with patch("app.api.routes.run.docker.from_env", return_value=fake_client):
            result = _execute_python_in_docker(
                code="print('hello')",
                stdin="",
                timeout_seconds=3,
            )

        self.assertEqual(result.stdout, "hello\n")
        self.assertEqual(result.stderr, "")
        self.assertEqual(result.exit_code, 0)
        self.assertFalse(result.timed_out)
        self.assertIsNotNone(fake_client.containers.container)
        self.assertTrue(fake_client.containers.container.removed)

    def test_execute_python_in_docker_pulls_image_when_missing(self) -> None:
        fake_client = FakeDockerClient(should_raise_not_found=True)

        with patch("app.api.routes.run.docker.from_env", return_value=fake_client):
            result = _execute_python_in_docker(
                code="print('hello')",
                stdin="",
                timeout_seconds=3,
            )

        self.assertEqual(result.exit_code, 0)
        self.assertTrue(fake_client.images.pulled)
