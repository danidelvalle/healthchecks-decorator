"""Test cases for the decorator module."""
import socket
from unittest.mock import call
from unittest.mock import patch

import pytest

from healthchecks_decorator import healthcheck
from healthchecks_decorator.decorator import _http_request


@pytest.fixture
def url() -> str:
    """Valid ping URL fixture."""
    return "https://fake-hc.com/0000-1111-2222-3333"


def test_minimal(url: str) -> None:
    """Test minimal decorator."""

    @healthcheck(url=url)
    def function_to_wrap() -> bool:
        return True

    with patch("healthchecks_decorator.decorator.urlopen") as urlopen_mock:

        assert function_to_wrap()
        urlopen_mock.assert_called_once_with(url, timeout=10)


def test_with_send_start(url: str) -> None:
    """Test sending a start signal."""

    @healthcheck(url=url, send_start=True)
    def function_with_arg(param: str) -> bool:
        return len(param) > 0

    with patch("healthchecks_decorator.decorator.urlopen") as urlopen_mock:
        assert function_with_arg("test")
        expected_calls = [
            call(f"{url}/start", timeout=10),
            call(url, timeout=10),
        ]
        urlopen_mock.assert_has_calls(expected_calls)


def test_exception(url: str) -> None:
    """Test having an exception at urlopen."""

    @healthcheck(url=url)
    def function_with_failing_healthcheck() -> bool:
        return True

    with patch("healthchecks_decorator.decorator.urlopen") as urlopen_mock:
        urlopen_mock.side_effect = socket.error()
        assert function_with_failing_healthcheck()


def test_wrapped_exception(url: str) -> None:
    """Test a failure scenario when the wrapped function raises an exception."""

    @healthcheck(url=url)
    def function_that_raises_exception() -> bool:
        raise Exception("inner exception")

    with patch("healthchecks_decorator.decorator.urlopen") as urlopen_mock:
        with pytest.raises(Exception):
            function_that_raises_exception()
        urlopen_mock.assert_called_once_with(url + "/fail", timeout=10)


def test_wrong_url_schema() -> None:
    """Test invalid URL schemas."""
    with pytest.raises(ValueError):
        _http_request("file:///tmp/localfile.txt")
