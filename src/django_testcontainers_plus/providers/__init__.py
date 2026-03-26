from .base import ContainerProvider
from .mailhog import MailhogProvider
from .postgres import PostgresProvider

__all__ = [
    "ContainerProvider",
    "MailhogProvider",
    "PostgresProvider",
    "PROVIDER_REGISTRY",
    "UNAVAILABLE_PROVIDERS",
]

PROVIDER_REGISTRY: list[ContainerProvider] = [
    PostgresProvider(),
    MailhogProvider(),
]

UNAVAILABLE_PROVIDERS: dict[str, tuple[str, Exception]] = {}

try:
    from .mysql import MySQLProvider

    PROVIDER_REGISTRY.append(MySQLProvider())
    __all__.append("MySQLProvider")
except ImportError as e:
    UNAVAILABLE_PROVIDERS["mysql"] = ("mysql", e)

try:
    from .redis import RedisProvider

    PROVIDER_REGISTRY.append(RedisProvider())
    __all__.append("RedisProvider")
except ImportError as e:
    UNAVAILABLE_PROVIDERS["redis"] = ("redis", e)

try:
    from .s3 import S3Provider

    PROVIDER_REGISTRY.append(S3Provider())
    __all__.append("S3Provider")
except ImportError as e:
    UNAVAILABLE_PROVIDERS["s3"] = ("s3", e)
