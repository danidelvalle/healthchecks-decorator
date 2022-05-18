"""Test cases for the decorator module."""
import socket
from unittest.mock import call
from unittest.mock import patch

import pytest

from healthchecks_decorator import healthcheck
from healthchecks_decorator.decorator import _http_request


@pytest.fixture
def host() -> str:
    """Valid host fixture."""
    return "https://fake-hc.com"


@pytest.fixture
def uuid_working() -> str:
    """Valid UUID fixture."""
    return "0000-1111-2222-3333"


def test_minimal(host: str, uuid_working: str) -> None:
    """Test minimal decorator."""

    @healthcheck(uuid=uuid_working, host=host)
    def function_to_wrap() -> bool:
        return True

    with patch("healthchecks_decorator.decorator.urlopen") as urlopen_mock:

        assert function_to_wrap()
        urlopen_mock.assert_called_once_with(f"{host}/{uuid_working}", timeout=10)


def test_with_send_start(host: str, uuid_working: str) -> None:
    """Test sending a start signal."""

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
    """Test having an exception at urlopen."""

    @healthcheck(uuid=uuid_working, host=host)
    def function_with_failing_healthcheck() -> bool:
        return True

    with patch("healthchecks_decorator.decorator.urlopen") as urlopen_mock:
        urlopen_mock.side_effect = socket.error()
        assert function_with_failing_healthcheck()


def test_wrong_url_schema() -> None:
    """Test invalid URL schemas."""
    with pytest.raises(ValueError):
        _http_request("file:///tmp/localfile.txt")
