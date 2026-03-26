"""Integration tests for S3Provider with a real RustFS container."""

import boto3
import pytest
from botocore.exceptions import ClientError

from django_testcontainers_plus.providers.s3 import S3Provider
from tests.test_s3_provider import MockSettings


class TestS3Integration:
    """Test S3Provider against a real RustFS container."""

    @pytest.fixture(scope="class", autouse=True)
    def s3_container(self, request):
        """Start a real RustFS container for the test class."""
        provider = S3Provider()
        config = provider.get_default_config()
        container = provider.get_container(config)
        container.start()
        host = container.get_container_host_ip()
        port = container.get_exposed_port(9000)

        request.cls.container = container
        request.cls.endpoint_url = f"http://{host}:{port}"

        yield

        container.stop()

    def _get_client(self):
        return boto3.client(
            "s3",
            endpoint_url=self.endpoint_url,
            aws_access_key_id="rustfsadmin",
            aws_secret_access_key="rustfsadmin",
        )

    def test_container_starts_and_accepts_connections(self):
        client = self._get_client()
        response = client.list_buckets()
        assert "Buckets" in response

    def test_create_bucket(self):
        client = self._get_client()
        client.create_bucket(Bucket="integration-test")
        buckets = [b["Name"] for b in client.list_buckets()["Buckets"]]
        assert "integration-test" in buckets

    def test_put_and_get_object(self):
        client = self._get_client()
        client.create_bucket(Bucket="object-test")
        client.put_object(Bucket="object-test", Key="hello.txt", Body=b"hello world")

        obj = client.get_object(Bucket="object-test", Key="hello.txt")
        assert obj["Body"].read() == b"hello world"

    def test_delete_object(self):
        client = self._get_client()
        client.create_bucket(Bucket="delete-test")
        client.put_object(Bucket="delete-test", Key="temp.txt", Body=b"temporary")
        client.delete_object(Bucket="delete-test", Key="temp.txt")

        with pytest.raises(ClientError) as exc_info:
            client.get_object(Bucket="delete-test", Key="temp.txt")
        assert exc_info.value.response["Error"]["Code"] == "NoSuchKey"

    def test_provider_update_settings_creates_bucket(self):
        """Test the full update_settings flow with a real container."""
        settings = MockSettings(AWS_STORAGE_BUCKET_NAME="auto-created")
        provider = S3Provider()
        config = provider.get_default_config()

        updates = provider.update_settings(self.container, settings, config)

        assert updates["AWS_S3_ENDPOINT_URL"] == self.endpoint_url

        # Verify bucket was actually created
        client = self._get_client()
        buckets = [b["Name"] for b in client.list_buckets()["Buckets"]]
        assert "auto-created" in buckets
