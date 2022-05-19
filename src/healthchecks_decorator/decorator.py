"""Healthchecks Decorator."""
import typing as t
from functools import partial
from functools import wraps
from urllib.request import urlopen

WrappedFn = t.TypeVar("WrappedFn", bound=t.Callable[..., t.Any])


def _http_request(endpoint: str, timeout: t.Optional[int] = 10) -> bool:
    """Send a ping request using standard library `urllib.parse.urlopen`.

    Args:
        endpoint (str): Full URL of the check.
        timeout (int, optional): Connection timeout in seconds. Defaults to 10.

    Raises:
        ValueError: if the endpoint schema is not http or https

    Returns:
        bool: True if the request succeeded, False otherwise.
    """
    try:
        if endpoint.lower().startswith("http"):
            # Bandit will still complain, so S310 is omitted
            urlopen(endpoint, timeout=timeout)  # noqa: S310
            return True
        else:
            raise ValueError("Only http[s] schemes allowed.") from None
    except OSError:
        return False


@t.overload
def healthcheck(func: WrappedFn) -> WrappedFn:  # noqa: D103
    pass


@t.overload
def healthcheck(  # noqa: D103
    *, url: str, send_start: bool = False
) -> t.Callable[[WrappedFn], WrappedFn]:
    pass


def healthcheck(
    func: t.Union[WrappedFn, None] = None,
    *,
    url: str = "",
    send_start: bool = False,
) -> t.Union[WrappedFn, t.Callable[[WrappedFn], WrappedFn]]:
    """Healthcheck decorator.

    Args:
        func (t.Union[WrappedFn, None], optional): The function to decorate. Defaults to None.
        url (str): The ping URL (e.g.: "https://hc-ping.com/<uuid>"). Must start with `http`.
        send_start (bool): Whether to send a '/start' signal. Defaults to False.

    Returns:
        t.Union[WrappedFn, t.Callable[[WrappedFn], WrappedFn]]: A wrapped function.
    """
    if func is None:
        return t.cast(WrappedFn, partial(healthcheck, url=url, send_start=send_start))

    @wraps(func)
    def healthcheck_wrapper(*args: t.Any, **kwargs: t.Any) -> t.Any:
        if send_start:
            sep = "" if url.endswith("/") else "/"
            url_with_start = f"{url}{sep}start"
            _http_request(url_with_start)
        wrapped_result = func(*args, **kwargs)  # type: ignore
        _http_request(url)
        return wrapped_result

    return t.cast(WrappedFn, healthcheck_wrapper)
