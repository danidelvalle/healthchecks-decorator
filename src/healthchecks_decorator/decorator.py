"""Healthchecks Decorator."""
import logging
import typing as t
from dataclasses import dataclass
from functools import partial
from functools import wraps
from os import getenv
from urllib.parse import urlencode
from urllib.parse import urlparse
from urllib.parse import urlunparse
from urllib.request import urlopen

WrappedFn = t.TypeVar("WrappedFn", bound=t.Callable[..., t.Any])

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


ENV_VAR_PREFIX = "HEALTHCHECK"
VALID_URL_SCHEMES = ("http", "https")


@dataclass
class HealthcheckConfig:
    """Healthecheks config."""

    url: t.Optional[str]
    send_start: t.Optional[bool]
    send_diagnostics: t.Optional[bool]

    def _build_url_with_path(self, path: str) -> str:
        """Build a sub URL."""
        parsed_url = urlparse(self.url)
        sep = "" if parsed_url.path.endswith("/") else "/"  # type: ignore
        new_path = parsed_url.path + sep + path  # type: ignore
        new_url = urlunparse(
            (  # type: ignore
                parsed_url.scheme,
                parsed_url.netloc,
                new_path,
                parsed_url.params,
                parsed_url.query,
                parsed_url.fragment,
            )
        )
        return new_url  # type: ignore

    @property
    def start_url(self) -> str:
        """Return the start URL."""
        return self._build_url_with_path("start")

    @property
    def fail_url(self) -> str:
        """Return the fail URL."""
        return self._build_url_with_path("fail")

    def __bool__(self) -> bool:
        """Return True if the config is valid, False otherwise."""
        if not self.url:
            logging.warning("Missing URL")
            return False

        try:
            parsed_url = urlparse(self.url)

            if parsed_url.scheme not in VALID_URL_SCHEMES:
                logging.warning(f"Invalid URL scheme for URL: {self.url}")
                return False

            if not parsed_url.netloc:
                logging.warning(f"Invalid netloc for URL: {self.url}")
                return False
            return True
        except AttributeError:
            logging.warning(f"Invalid URL: {self.url}")
            return False

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

    Returns:
        bool: True if the request succeeded, False otherwise.
    """
    try:
        # Bandit will still complain, so S310 is omitted
        urlopen(endpoint, data=data, timeout=timeout)  # noqa: S310
        return True
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

    if not config:
        log.warning("Disabling @healthcheck: invalid config")
        return func

    @wraps(func)
    def healthcheck_wrapper(*args: t.Any, **kwargs: t.Any) -> t.Any:
        assert config.url is not None  # noqa: S101
        if config.send_start:
            _http_request(config.start_url)

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
            _http_request(config.fail_url)
            raise e

    return t.cast(WrappedFn, healthcheck_wrapper)
