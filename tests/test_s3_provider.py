"""Tests for S3Provider."""

from unittest.mock import Mock, patch

import pytest
from botocore.exceptions import ClientError

from django_testcontainers_plus.providers.s3 import S3Provider


class MockSettings:
    """Mock Django settings object."""

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


def _mock_container(host="127.0.0.1", api_port=32768, console_port=32769):
    """Create a mock container with standard port mappings."""
    container = Mock()
    container.get_container_host_ip.return_value = host
    port_map = {9000: api_port, 9001: console_port}
    container.get_exposed_port.side_effect = lambda p: port_map[p]
    return container


class TestS3Provider:
    """Test S3Provider class."""

    def test_name(self):
        provider = S3Provider()
        assert provider.name == "s3"

    # --- Auto-detection tests ---

    def test_can_auto_detect_storages_s3boto3(self):
        settings = MockSettings(
            STORAGES={
                "default": {
                    "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
                }
            }
        )
        assert S3Provider().can_auto_detect(settings) is True

    def test_can_auto_detect_staticfiles_s3(self):
        settings = MockSettings(
            STORAGES={
                "staticfiles": {
                    "BACKEND": "storages.backends.s3boto3.S3StaticStorage",
                }
            }
        )
        assert S3Provider().can_auto_detect(settings) is True

    def test_can_auto_detect_legacy_default_file_storage(self):
        settings = MockSettings(DEFAULT_FILE_STORAGE="storages.backends.s3boto3.S3Boto3Storage")
        assert S3Provider().can_auto_detect(settings) is True

    def test_can_auto_detect_aws_bucket_name(self):
        settings = MockSettings(AWS_STORAGE_BUCKET_NAME="my-bucket")
        assert S3Provider().can_auto_detect(settings) is True

    def test_can_auto_detect_no_s3_config(self):
        settings = MockSettings()
        assert S3Provider().can_auto_detect(settings) is False

    def test_can_auto_detect_non_s3_storage(self):
        settings = MockSettings(
            STORAGES={
                "default": {
                    "BACKEND": "django.core.files.storage.FileSystemStorage",
                }
            }
        )
        assert S3Provider().can_auto_detect(settings) is False

    def test_can_auto_detect_empty_bucket_name(self):
        settings = MockSettings(AWS_STORAGE_BUCKET_NAME="")
        assert S3Provider().can_auto_detect(settings) is False

    def test_can_auto_detect_storages_not_dict(self):
        settings = MockSettings(STORAGES="not-a-dict")
        assert S3Provider().can_auto_detect(settings) is False

    # --- Container creation tests ---

    @patch("django_testcontainers_plus.providers.s3.DockerContainer")
    def test_get_container_defaults(self, mock_docker_container):
        mock_instance = Mock()
        mock_instance.with_exposed_ports.return_value = mock_instance
        mock_instance.with_env.return_value = mock_instance
        mock_instance.with_command.return_value = mock_instance
        mock_docker_container.return_value = mock_instance

        provider = S3Provider()
        container = provider.get_container(provider.get_default_config())

        # Verify the image used
        assert mock_docker_container.call_args[0][0] == "rustfs/rustfs"

        # Verify ports and command via the chain
        assert mock_instance.with_exposed_ports.call_args[0] == (9000, 9001)
        assert mock_instance.with_command.call_args[0] == ("/data",)

        # Verify env vars were set by collecting all with_env calls
        env_calls = {call[0][0]: call[0][1] for call in mock_instance.with_env.call_args_list}
        assert env_calls["RUSTFS_ACCESS_KEY"] == "rustfsadmin"
        assert env_calls["RUSTFS_SECRET_KEY"] == "rustfsadmin"
        assert env_calls["RUSTFS_CONSOLE_ENABLE"] == "true"
        assert container == mock_instance

    @patch("django_testcontainers_plus.providers.s3.DockerContainer")
    def test_get_container_custom_image(self, mock_docker_container):
        mock_instance = Mock()
        mock_instance.with_exposed_ports.return_value = mock_instance
        mock_instance.with_env.return_value = mock_instance
        mock_instance.with_command.return_value = mock_instance
        mock_docker_container.return_value = mock_instance

        config = {
            "image": "dxflrs/garage",
            "access_key": "rustfsadmin",
            "secret_key": "rustfsadmin",
        }
        S3Provider().get_container(config)

        assert mock_docker_container.call_args[0][0] == "dxflrs/garage"

    @patch("django_testcontainers_plus.providers.s3.DockerContainer")
    def test_get_container_custom_credentials(self, mock_docker_container):
        mock_instance = Mock()
        mock_instance.with_exposed_ports.return_value = mock_instance
        mock_instance.with_env.return_value = mock_instance
        mock_instance.with_command.return_value = mock_instance
        mock_docker_container.return_value = mock_instance

        S3Provider().get_container({"access_key": "mykey", "secret_key": "mysecret"})

        env_calls = {call[0][0]: call[0][1] for call in mock_instance.with_env.call_args_list}
        assert env_calls["RUSTFS_ACCESS_KEY"] == "mykey"
        assert env_calls["RUSTFS_SECRET_KEY"] == "mysecret"

    @patch("django_testcontainers_plus.providers.s3.DockerContainer")
    def test_get_container_with_environment(self, mock_docker_container):
        mock_instance = Mock()
        mock_instance.with_exposed_ports.return_value = mock_instance
        mock_instance.with_env.return_value = mock_instance
        mock_instance.with_command.return_value = mock_instance
        mock_docker_container.return_value = mock_instance

        config = {
            "access_key": "rustfsadmin",
            "secret_key": "rustfsadmin",
            "environment": {
                "RUSTFS_ADDRESS": ":9000",
                "RUSTFS_SERVER_DOMAINS": "example.com",
            },
        }
        S3Provider().get_container(config)

        env_calls = {call[0][0]: call[0][1] for call in mock_instance.with_env.call_args_list}
        assert env_calls["RUSTFS_ADDRESS"] == ":9000"
        assert env_calls["RUSTFS_SERVER_DOMAINS"] == "example.com"

    # --- Settings update tests (bucket creation patched out) ---

    @patch.object(S3Provider, "_create_bucket")
    def test_update_settings(self, mock_create_bucket):
        settings = MockSettings(AWS_STORAGE_BUCKET_NAME="test-uploads")
        config = S3Provider().get_default_config()

        updates = S3Provider().update_settings(_mock_container(), settings, config)

        assert updates["AWS_S3_ENDPOINT_URL"] == "http://127.0.0.1:32768"
        assert updates["S3_CONSOLE_URL"] == "http://127.0.0.1:32769"
        assert updates["AWS_ACCESS_KEY_ID"] == "rustfsadmin"
        assert updates["AWS_SECRET_ACCESS_KEY"] == "rustfsadmin"

    @patch.object(S3Provider, "_create_bucket")
    def test_update_settings_overrides_existing_credentials(self, mock_create_bucket):
        settings = MockSettings(
            AWS_ACCESS_KEY_ID="existing-key",
            AWS_SECRET_ACCESS_KEY="existing-secret",
            AWS_STORAGE_BUCKET_NAME="my-bucket",
        )
        config = S3Provider().get_default_config()

        updates = S3Provider().update_settings(_mock_container(), settings, config)

        assert updates["AWS_ACCESS_KEY_ID"] == "rustfsadmin"
        assert updates["AWS_SECRET_ACCESS_KEY"] == "rustfsadmin"

    @patch.object(S3Provider, "_create_bucket")
    def test_update_settings_default_bucket(self, mock_create_bucket):
        settings = MockSettings()
        config = S3Provider().get_default_config()

        updates = S3Provider().update_settings(_mock_container(), settings, config)

        assert updates["AWS_STORAGE_BUCKET_NAME"] == "test-bucket"

    @patch.object(S3Provider, "_create_bucket")
    def test_update_settings_config_bucket_name(self, mock_create_bucket):
        settings = MockSettings()
        config = {**S3Provider().get_default_config(), "bucket_name": "custom-bucket"}

        updates = S3Provider().update_settings(_mock_container(), settings, config)

        assert updates["AWS_STORAGE_BUCKET_NAME"] == "custom-bucket"

    @patch.object(S3Provider, "_create_bucket")
    def test_update_settings_skips_bucket_name_when_already_set(self, mock_create_bucket):
        settings = MockSettings(AWS_STORAGE_BUCKET_NAME="existing-bucket")
        config = S3Provider().get_default_config()

        updates = S3Provider().update_settings(_mock_container(), settings, config)

        assert "AWS_STORAGE_BUCKET_NAME" not in updates

    # --- Bucket creation tests ---

    @patch("boto3.client")
    def test_create_bucket(self, mock_boto3_client):
        mock_s3 = Mock()
        mock_boto3_client.return_value = mock_s3

        S3Provider()._create_bucket(
            "http://localhost:9000", "rustfsadmin", "rustfsadmin", "my-bucket"
        )

        created_bucket = mock_s3.create_bucket.call_args[1]["Bucket"]
        assert created_bucket == "my-bucket"

    @patch("boto3.client")
    def test_create_bucket_already_exists(self, mock_boto3_client):
        mock_s3 = Mock()
        mock_s3.create_bucket.side_effect = ClientError(
            {"Error": {"Code": "BucketAlreadyOwnedByYou", "Message": ""}},
            "CreateBucket",
        )
        mock_boto3_client.return_value = mock_s3

        # Should not raise
        S3Provider()._create_bucket(
            "http://localhost:9000", "rustfsadmin", "rustfsadmin", "my-bucket"
        )

    @patch("boto3.client")
    def test_create_bucket_unexpected_error_raises(self, mock_boto3_client):
        mock_s3 = Mock()
        mock_s3.create_bucket.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "Access Denied"}},
            "CreateBucket",
        )
        mock_boto3_client.return_value = mock_s3

        with pytest.raises(ClientError):
            S3Provider()._create_bucket(
                "http://localhost:9000", "rustfsadmin", "rustfsadmin", "my-bucket"
            )

    # --- Default config test ---

    def test_get_default_config(self):
        config = S3Provider().get_default_config()

        assert config == {
            "image": "rustfs/rustfs",
            "access_key": "rustfsadmin",
            "secret_key": "rustfsadmin",
            "bucket_name": "test-bucket",
        }
