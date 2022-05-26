"""Test cases for the decorator module."""
import socket
import typing as t
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
        urlopen_mock.assert_called_once_with(url, data=None, timeout=10)


def test_with_send_start(url: str) -> None:
    """Test sending a start signal."""

    @healthcheck(url=url, send_start=True)
    def function_with_arg(param: str) -> bool:
        return len(param) > 0

    with patch("healthchecks_decorator.decorator.urlopen") as urlopen_mock:
        assert function_with_arg("test")
        expected_calls = [
            call(f"{url}/start", data=None, timeout=10),
            call(url, data=None, timeout=10),
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
        urlopen_mock.assert_called_once_with(url + "/fail", data=None, timeout=10)


def test_missing_url() -> None:
    """Test that nothing happens if the url is not defined (None or empty)."""

    def func() -> bool:
        return True

    with patch("healthchecks_decorator.decorator.urlopen") as urlopen_mock:
        assert healthcheck(url=None)(func)()  # type: ignore
        urlopen_mock.assert_not_called()

        assert healthcheck(url="")(func)()
        urlopen_mock.assert_not_called()


def test_diagnostics(url: str) -> None:
    """Test sending diagnostics."""
    diagnostics = {"foo": "bar"}

    @healthcheck(url=url, send_diagnostics=True)
    def f(diag: t.Any) -> t.Any:
        return diag

    with patch("healthchecks_decorator.decorator.urlopen") as urlopen_mock:
        assert f(diagnostics) == diagnostics
        expected_data = b"foo=bar"
        urlopen_mock.assert_called_once_with(url, data=expected_data, timeout=10)

    with patch("healthchecks_decorator.decorator.urlopen") as urlopen_mock:
        # invalid diagnostics should not crash our wrapped func
        invalid_diag = "not a valid non-string sequence or mapping object"
        assert f(invalid_diag) == invalid_diag
        urlopen_mock.assert_called_once_with(url, data=None, timeout=10)


def test_wrong_url_schema() -> None:
    """Test invalid URL schemas."""
    with pytest.raises(ValueError):
        _http_request("file:///tmp/localfile.txt")
