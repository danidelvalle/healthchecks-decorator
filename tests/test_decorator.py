"""Test cases for the decorator module."""
import pytest
from unittest.mock import patch, MagicMock, call
import socket
from healthchecks_decorator import healthcheck


@pytest.fixture
def host() -> str:
    return "https://fake-hc.com"


@pytest.fixture
def uuid_working() -> str:
    return "0000-1111-2222-3333"


def test_minimal(host: str, uuid_working: str) -> None:
    """It exits with a status code of zero."""

    @healthcheck(uuid=uuid_working, host=host)
    def function_to_wrap() -> bool:
        return True

    with patch("healthchecks_decorator.decorator.urlopen") as urlopen_mock:

        assert function_to_wrap()
        urlopen_mock.assert_called_once_with(f"{host}/{uuid_working}", timeout=10)


def test_with_send_start(host: str, uuid_working: str) -> None:
    @healthcheck(uuid=uuid_working, host=host, send_start=True)
    def function_with_arg(param: str) -> bool:
        return len(param) > 0

    with patch("healthchecks_decorator.decorator.urlopen") as urlopen_mock:
        assert function_with_arg("test")
        expected_calls = [
            call(f"{host}/{uuid_working}/start", timeout=10),
            call(f"{host}/{uuid_working}", timeout=10),
        ]
        urlopen_mock.assert_has_calls(expected_calls)


def test_exception(host: str, uuid_working: str) -> None:
    @healthcheck(uuid=uuid_working, host=host)
    def function_with_failing_healthcheck() -> bool:
        return True

    with patch("healthchecks_decorator.decorator.urlopen") as urlopen_mock:
        urlopen_mock.side_effect = socket.error()
        assert function_with_failing_healthcheck()
