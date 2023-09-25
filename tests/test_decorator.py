"""Test cases for the decorator module."""
import socket
import typing as t
from os import environ
from unittest.mock import call
from unittest.mock import patch

import pytest

from healthchecks_decorator import healthcheck
from healthchecks_decorator.decorator import HealthcheckConfig


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


def test_minimalist(url: str) -> None:
    """Test the most minimalist usage with env vars."""
    environ["HEALTHCHECK_URL"] = url

    @healthcheck
    def func() -> bool:
        return True

    with patch("healthchecks_decorator.decorator.urlopen") as urlopen_mock:
        assert func()
        urlopen_mock.assert_called_once_with(url, data=None, timeout=10)

    del environ["HEALTHCHECK_URL"]


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
        assert healthcheck(url=None)(func)()
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


def test_url_with_query() -> None:
    """Test urls with queries, as '?create=1'."""
    slug_url = "https://hc-ping.com/fqOOd6-F4MMNuCEnzTU01w/db-backups?create=1"
    c = HealthcheckConfig(url=slug_url, send_start=True, send_diagnostics=False)
    assert c.url == slug_url
    assert (
        c.start_url
        == "https://hc-ping.com/fqOOd6-F4MMNuCEnzTU01w/db-backups/start?create=1"
    )
    assert (
        c.fail_url
        == "https://hc-ping.com/fqOOd6-F4MMNuCEnzTU01w/db-backups/fail?create=1"
    )


def test_invalid_url() -> None:
    """Test invalid URL schemas."""
    args = dict(send_start=True, send_diagnostics=False)

    # Valid URL
    assert (
        bool(HealthcheckConfig(url="https://fake-hc.com/0000-1111-2222-3333", **args))
        is True
    )

    # Empty or None URL
    assert bool(HealthcheckConfig(url="", **args)) is False
    assert bool(HealthcheckConfig(url=None, **args)) is False

    # Non-HTTP(S) scheme
    assert (
        bool(HealthcheckConfig(url="ftp://fake-hc.com/0000-1111-2222-3333", **args))
        is False
    )

    # No scheme
    assert bool(HealthcheckConfig(url="dkakasdkjdjakdjadjfalskdjfalk", **args)) is False

    # No netloc
    assert bool(HealthcheckConfig(url="https://", **args)) is False

    # Wrong type
    assert bool(HealthcheckConfig(url=123.23, **args)) is False  # type: ignore


def test_envvars(url: str) -> None:
    """Test configuring with env vars."""
    # No explicit settings + no env vars => defaults
    c = HealthcheckConfig(url=None, send_diagnostics=None, send_start=None)
    assert c.send_diagnostics is False
    assert c.send_start is False
    assert c.url is None

    # Set some env vars

    # No explicit settings + env vars => env vars
    environ["HEALTHCHECK_URL"] = url
    environ["HEALTHCHECK_SEND_DIAGNOSTICS"] = "TRue"  # case should not affect
    environ["HEALTHCHECK_SEND_START"] = "1"  # this should alse be True
    c = HealthcheckConfig(url=None, send_diagnostics=None, send_start=None)
    assert c.send_diagnostics is True
    assert c.send_start is True
    assert c.url == url

    # explicit settings + env vars => explicit settings
    other_url = url + "/other"
    c = HealthcheckConfig(url=other_url, send_diagnostics=False, send_start=False)
    assert c.send_diagnostics is False
    assert c.send_start is False
    assert c.url == other_url

    del environ["HEALTHCHECK_URL"]
    del environ["HEALTHCHECK_SEND_DIAGNOSTICS"]
    del environ["HEALTHCHECK_SEND_START"]
