import unittest
import sys
from pathlib import Path
from unittest.mock import patch

from docker.errors import ImageNotFound

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.api.routes.run import _execute_python_in_docker
from app.core.settings import settings


class FakeContainer:
    def __init__(self, kwargs: dict) -> None:
        self.kwargs = kwargs
        self.status = "created"
        self.id = "fake-container"
        self.attrs = {"State": {"ExitCode": 0}}
        self.removed = False

    def start(self) -> None:
        self.status = "running"

    def exec_run(self, **kwargs):
        class FakeExecResult:
            def __init__(self) -> None:
                self.output = (b"hello\n", b"")
                self.exit_code = 0

        return FakeExecResult()

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

    def test_execute_python_in_docker_applies_sandbox_limits(self) -> None:
        fake_client = FakeDockerClient()

        with patch("app.api.routes.run.docker.from_env", return_value=fake_client):
            _execute_python_in_docker(
                code="print('hello')",
                stdin="",
                timeout_seconds=3,
            )

        create_kwargs = fake_client.containers.created_kwargs
        self.assertIsNotNone(create_kwargs)
        assert create_kwargs is not None
        self.assertTrue(create_kwargs["network_disabled"])
        self.assertEqual(create_kwargs["mem_limit"], settings.sandbox_memory_limit)
        self.assertEqual(create_kwargs["nano_cpus"], settings.sandbox_cpu_nano)
        self.assertEqual(create_kwargs["pids_limit"], settings.sandbox_pids_limit)
        self.assertTrue(create_kwargs["read_only"])
        self.assertEqual(create_kwargs["user"], settings.sandbox_user)
        self.assertEqual(
            create_kwargs["tmpfs"],
            {
                settings.sandbox_workdir: (
                    f"rw,noexec,nosuid,nodev,size={settings.sandbox_tmpfs_size}"
                ),
            },
        )
        self.assertEqual(create_kwargs["cap_drop"], ["ALL"])
        self.assertEqual(create_kwargs["security_opt"], ["no-new-privileges"])
