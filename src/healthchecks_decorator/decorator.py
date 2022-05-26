"""Healthchecks Decorator."""
import logging
import typing as t
from functools import partial
from functools import wraps
from urllib.parse import urlencode
from urllib.request import urlopen

WrappedFn = t.TypeVar("WrappedFn", bound=t.Callable[..., t.Any])

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


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
    *, url: str, send_start: bool = False, send_diagnostics: bool = False
) -> t.Callable[[WrappedFn], WrappedFn]:
    pass


def healthcheck(
    func: t.Union[WrappedFn, None] = None,
    *,
    url: str = "",
    send_start: bool = False,
    send_diagnostics: bool = False,
) -> t.Union[WrappedFn, t.Callable[[WrappedFn], WrappedFn]]:
    """Healthcheck decorator.

    Args:
        func (t.Union[WrappedFn, None], optional): The function to decorate. Defaults to None.
        url (str): The ping URL (e.g.: "https://hc-ping.com/<uuid>"). Must start with `http`.
        send_start (bool): Whether to send a '/start' signal. Defaults to False.
        send_diagnostics (bool): When enabled, send the wrapped function returned value as diagnostics information.
                                 Defaults to False.

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

    if url is None or not len(url):
        log.warning("Disabling @healthcheck: 'url' argument is not provided")
        return func

    sep = "" if url.endswith("/") else "/"

    @wraps(func)
    def healthcheck_wrapper(*args: t.Any, **kwargs: t.Any) -> t.Any:
        if send_start:
            url_with_start = f"{url}{sep}start"
            _http_request(url_with_start)

        try:
            wrapped_result = func(*args, **kwargs)  # type: ignore
            _http_request(
                url,
                data=_validate_diagnostics(wrapped_result)
                if send_diagnostics
                else None,
            )
            return wrapped_result
        except Exception as e:
            url_with_fail = f"{url}{sep}fail"
            _http_request(url_with_fail)
            raise e

    return t.cast(WrappedFn, healthcheck_wrapper)
