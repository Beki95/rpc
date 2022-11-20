import abc  # noqa
import typing

from aio_pika.abc import (
    Arguments,  # noqa
    TimeoutType,
)


class RPCRouterProtocol(abc.ABC):

    @abc.abstractmethod
    def __init__(self, *, prefix: str = '') -> None:  # noqa
        raise NotImplementedError

    @abc.abstractclassmethod
    def validate_prefix(cls, prefix: str):
        raise NotImplementedError

    @abc.abstractmethod
    def add_rpc_route(
            self,
            path: str,
            endpoint: typing.Callable[..., typing.Any],
            **kwargs
    ):
        raise NotImplementedError

    @abc.abstractmethod
    def rpc_route(self, path: str, **kwargs):
        raise NotImplementedError

    @abc.abstractmethod
    def include_route(self, router: 'RPCRouter', *, prefix: str = ''):
        raise NotImplementedError

    @abc.abstractmethod
    def procedure(
            self,
            path: str,
            *,
            durable: bool = False,
            exclusive: bool = False,
            passive: bool = False,
            auto_delete: bool = False,
            arguments: Arguments = None,
            timeout: TimeoutType = None,
    ):
        raise NotImplementedError


class RPCRouter(RPCRouterProtocol):

    def __init__(self, *, prefix: str = '') -> None:
        if prefix:
            self.validate_prefix(prefix)
        self.routes: list[dict[str, typing.Any]] = []
        self.prefix: str = prefix

    @classmethod
    def validate_prefix(cls, prefix: str):
        assert prefix.startswith('/'), 'A path prefix must start with "/"'
        assert not prefix.endswith('/'), 'A path prefix must not end with "/"'

    def add_rpc_route(
            self,
            path: str,
            endpoint: typing.Callable[..., typing.Any],
            **kwargs
    ):
        self.routes.append(
            dict(path=path, endpoint=endpoint, kwargs=kwargs)
        )

    def rpc_route(self, path: str, **kwargs):
        def wrapper(endpoint: typing.Callable[..., typing.Any]):
            self.add_rpc_route(path, endpoint, **kwargs)
            return endpoint

        return wrapper

    def include_route(self, router: 'RPCRouter', *, prefix: str = ''):
        if prefix:
            self.validate_prefix(prefix)
        for route in router.routes:
            path = self.prefix + prefix + route['path']
            self.add_rpc_route(
                path.replace('/', '_'), route['endpoint'], **route['kwargs'],
            )

    def procedure(
            self,
            path: str,
            *,
            durable: bool = False,
            exclusive: bool = False,
            passive: bool = False,
            auto_delete: bool = False,
            arguments: Arguments = None,
            timeout: TimeoutType = None,
    ):
        return self.rpc_route(
            path=path,
            durable=durable,
            exclusive=exclusive,
            passive=passive,
            auto_delete=auto_delete,
            arguments=arguments or {},
            timeout=timeout,
        )
