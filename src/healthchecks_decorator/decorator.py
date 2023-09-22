"""Healthchecks Decorator."""
import logging
import typing as t
from dataclasses import dataclass
from functools import partial
from functools import wraps
from os import getenv
from urllib.parse import urlencode
from urllib.request import urlopen

WrappedFn = t.TypeVar("WrappedFn", bound=t.Callable[..., t.Any])

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


ENV_VAR_PREFIX = "HEALTHCHECK"


@dataclass
class HealthcheckConfig:
    """Healthecheks config."""

    url: t.Optional[str]
    send_start: t.Optional[bool]
    send_diagnostics: t.Optional[bool]

    def __getattribute__(self, name: str) -> t.Any:
        """Overloaded to get info from environment variables or defaults when not defined."""
        candidate = super().__getattribute__(name)

        # [1] Return explicit values
        if candidate is not None:
            return candidate

        # [2] Env vars
        envvar_value = getenv(f"{ENV_VAR_PREFIX}_{name.upper()}")
        if envvar_value:
            return (
                envvar_value
                if name == "url"
                else envvar_value.strip().lower() in ("true", "1")
            )

        # [3] Return default values
        return None if name == "url" else False


def _http_request(
    endpoint: str,
    timeout: t.Optional[int] = 10,
    data: t.Optional[bytes] = None,
) -> bool:
    """Send a ping request using standard library `urllib.parse.urlopen`.

    Args:
        endpoint (str): Full URL of the check.
        timeout (int, optional): Connection timeout in seconds. Defaults to 10.
        data (bytes, optional): Optional diagnostic data. Defaults to None.

    Raises:
        ValueError: if the endpoint schema is not http or https

    Returns:
        bool: True if the request succeeded, False otherwise.
    """
    try:
        if endpoint.lower().startswith("http"):
            # Bandit will still complain, so S310 is omitted
            urlopen(endpoint, data=data, timeout=timeout)  # noqa: S310
            return True
        else:
            raise ValueError("Only http[s] schemes allowed.") from None
    except OSError:
        return False


def _validate_diagnostics(diag: t.Any) -> t.Optional[bytes]:
    try:
        return urlencode(diag).encode()
    except TypeError as te:
        log.warning(f"Ignoring diagnostics: {te}")
        return None


@t.overload
def healthcheck(func: WrappedFn) -> WrappedFn:  # noqa: D103
    pass


@t.overload
def healthcheck(  # noqa: D103
    *,
    url: t.Optional[str] = None,
    send_start: t.Optional[bool] = None,
    send_diagnostics: t.Optional[bool] = False,
) -> t.Callable[[WrappedFn], WrappedFn]:
    pass


def healthcheck(
    func: t.Union[WrappedFn, None] = None,
    *,
    url: t.Optional[str] = None,
    send_start: t.Optional[bool] = None,
    send_diagnostics: t.Optional[bool] = None,
) -> t.Union[WrappedFn, t.Callable[[WrappedFn], WrappedFn]]:
    """Healthcheck decorator.

    Args:
        func (t.Union[WrappedFn, None], optional): The function to decorate. Defaults to None.
        url (str): The ping URL (e.g.: "https://hc-ping.com/<uuid>"). Must start with `http`.
        send_start (bool, optional): Whether to send a '/start' signal. Defaults to False.
        send_diagnostics (bool, optional): When enabled, send the wrapped function returned value as
                                           diagnostics information. Defaults to False.

    Returns:
        t.Union[WrappedFn, t.Callable[[WrappedFn], WrappedFn]]: A wrapped function.
    """
    if func is None:
        return t.cast(
            WrappedFn,
            partial(
                healthcheck,
                url=url,
                send_start=send_start,
                send_diagnostics=send_diagnostics,
            ),
        )

    # Resolve the config combining explicit values, env vars and defaults
    config: HealthcheckConfig = HealthcheckConfig(
        url=url, send_diagnostics=send_diagnostics, send_start=send_start
    )

    if config.url is None or not len(config.url):
        log.warning("Disabling @healthcheck: 'url' argument is not provided")
        return func

    sep = "" if config.url.endswith("/") else "/"

    @wraps(func)
    def healthcheck_wrapper(*args: t.Any, **kwargs: t.Any) -> t.Any:
        assert config.url is not None  # noqa: S101
        if config.send_start:
            url_with_start = f"{config.url}{sep}start"
            _http_request(url_with_start)

        try:
            wrapped_result = func(*args, **kwargs)
            _http_request(
                config.url,
                data=_validate_diagnostics(wrapped_result)
                if config.send_diagnostics
                else None,
            )
            return wrapped_result
        except Exception as e:
            url_with_fail = f"{config.url}{sep}fail"
            _http_request(url_with_fail)
            raise e

    return t.cast(WrappedFn, healthcheck_wrapper)
