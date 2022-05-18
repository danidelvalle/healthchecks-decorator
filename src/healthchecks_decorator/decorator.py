from functools import wraps, partial
import socket
import typing as t
from urllib.request import urlopen
from urllib.parse import urljoin, quote_plus


WrappedFn = t.TypeVar("WrappedFn", bound=t.Callable[..., t.Any])


def http_request(endpoint: str, timeout: int = 10) -> bool:
    try:
        urlopen(endpoint, timeout=timeout)
        return True
    except socket.error as e:
        return False


def build_url(base: str, uuid: str, extra: str = "") -> str:

    full_url = urljoin(base, uuid)
    if extra:
        return f"{full_url}/{quote_plus(extra)}"
    return full_url


@t.overload
def healthcheck(func: WrappedFn) -> WrappedFn:
    pass


@t.overload
def healthcheck(
    *, uuid: str, host: str, send_start: bool = False
) -> t.Callable[[WrappedFn], WrappedFn]:
    pass


def healthcheck(
    func: t.Union[WrappedFn, None] = None,
    *,
    uuid: str = "",
    host: str = "https://hc-ping.com",
    send_start: bool = False,
) -> t.Union[WrappedFn, t.Callable[[WrappedFn], WrappedFn]]:
    if func is None:
        return t.cast(
            WrappedFn, partial(healthcheck, uuid=uuid, host=host, send_start=send_start)
        )

    @wraps(func)
    def healthcheck_wrapper(*args: t.Any, **kwargs: t.Any) -> t.Any:
        if send_start:
            http_request(build_url(host, uuid, "start"))
        wrapped_result = func(*args, **kwargs)  # type: ignore
        http_request(build_url(host, uuid))
        return wrapped_result

    return t.cast(WrappedFn, healthcheck_wrapper)
