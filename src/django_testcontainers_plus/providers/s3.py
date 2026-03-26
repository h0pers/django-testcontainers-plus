"""S3-compatible object storage provider using RustFS."""

import time
from typing import Any

import boto3
from botocore.exceptions import ClientError, EndpointConnectionError
from testcontainers.core.generic import DockerContainer

from .base import ContainerProvider

# Default ports for S3-compatible services
S3_API_PORT = 9000
CONSOLE_PORT = 9001

# Default credentials for RustFS
DEFAULT_ACCESS_KEY = "rustfsadmin"
DEFAULT_SECRET_KEY = "rustfsadmin"

DEFAULT_BUCKET_NAME = "test-bucket"


class S3Provider(ContainerProvider):
    """Provider for S3-compatible object storage containers (RustFS by default)."""

    @property
    def name(self) -> str:
        return "s3"

    def can_auto_detect(self, settings: Any, context: dict[str, Any] | None = None) -> bool:
        """Detect if S3 storage is configured in Django settings.

        Checks for:
        1. Django 4.2+ STORAGES setting with S3 backend
        2. Legacy DEFAULT_FILE_STORAGE with S3 backend
        3. AWS_STORAGE_BUCKET_NAME present (implies S3 usage)
        """
        # Check Django 4.2+ STORAGES setting
        storages = getattr(settings, "STORAGES", {})
        if isinstance(storages, dict):
            for storage_config in storages.values():
                if isinstance(storage_config, dict):
                    backend = str(storage_config.get("BACKEND", "")).lower()
                    if self._is_s3_backend(backend):
                        return True

        # Check legacy DEFAULT_FILE_STORAGE
        default_storage = str(getattr(settings, "DEFAULT_FILE_STORAGE", "")).lower()
        if self._is_s3_backend(default_storage):
            return True

        # Check for AWS_STORAGE_BUCKET_NAME (implies S3 usage)
        bucket_name = getattr(settings, "AWS_STORAGE_BUCKET_NAME", "")
        if bucket_name:
            return True

        return False

    def get_container(self, config: dict[str, Any]) -> DockerContainer:
        """Create S3-compatible container with configuration."""
        image = config.get("image", "rustfs/rustfs")
        access_key = config.get("access_key", DEFAULT_ACCESS_KEY)
        secret_key = config.get("secret_key", DEFAULT_SECRET_KEY)

        container = (
            DockerContainer(image)
            .with_exposed_ports(S3_API_PORT, CONSOLE_PORT)
            .with_env("RUSTFS_ACCESS_KEY", access_key)
            .with_env("RUSTFS_SECRET_KEY", secret_key)
            .with_env("RUSTFS_CONSOLE_ENABLE", "true")
            .with_command("/data")
        )

        env = config.get("environment", {})
        for key, value in env.items():
            container = container.with_env(key, value)

        return container

    def update_settings(
        self, container: DockerContainer, settings: Any, config: dict[str, Any]
    ) -> dict[str, Any]:
        """Update Django settings with container connection info and create bucket."""
        host = container.get_container_host_ip()
        api_port = container.get_exposed_port(S3_API_PORT)
        console_port = container.get_exposed_port(CONSOLE_PORT)

        access_key = config.get("access_key", DEFAULT_ACCESS_KEY)
        secret_key = config.get("secret_key", DEFAULT_SECRET_KEY)

        endpoint_url = f"http://{host}:{api_port}"

        updates: dict[str, Any] = {
            "AWS_S3_ENDPOINT_URL": endpoint_url,
            "AWS_ACCESS_KEY_ID": access_key,
            "AWS_SECRET_ACCESS_KEY": secret_key,
            "S3_CONSOLE_URL": f"http://{host}:{console_port}",
        }

        # Auto-create the bucket
        bucket_name = getattr(settings, "AWS_STORAGE_BUCKET_NAME", "") or config.get(
            "bucket_name", DEFAULT_BUCKET_NAME
        )
        self._create_bucket(endpoint_url, access_key, secret_key, bucket_name)

        # Ensure bucket name is set in settings
        if not getattr(settings, "AWS_STORAGE_BUCKET_NAME", ""):
            updates["AWS_STORAGE_BUCKET_NAME"] = bucket_name

        return updates

    def get_default_config(self) -> dict[str, Any]:
        return {
            "image": "rustfs/rustfs",
            "access_key": DEFAULT_ACCESS_KEY,
            "secret_key": DEFAULT_SECRET_KEY,
            "bucket_name": DEFAULT_BUCKET_NAME,
        }

    @staticmethod
    def _is_s3_backend(backend: str) -> bool:
        """Check if a backend string refers to an S3 storage backend."""
        return "s3boto3" in backend or "storages.backends.s3." in backend

    def _create_bucket(
        self,
        endpoint_url: str,
        access_key: str,
        secret_key: str,
        bucket_name: str,
        retries: int = 10,
        delay: float = 1.0,
    ) -> None:
        """Create the S3 bucket using boto3, retrying until the container is ready."""
        client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name="us-east-1",
        )

        for attempt in range(retries):
            try:
                client.create_bucket(Bucket=bucket_name)
                return
            except ClientError as e:
                if e.response["Error"]["Code"] == "BucketAlreadyOwnedByYou":
                    return
                raise
            except EndpointConnectionError:
                if attempt == retries - 1:
                    raise
                time.sleep(delay)
