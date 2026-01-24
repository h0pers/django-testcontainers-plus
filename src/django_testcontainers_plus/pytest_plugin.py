from typing import Any

import pytest

from .manager import ContainerManager

_container_manager: ContainerManager | None = None
_original_settings: dict[str, Any] = {}


@pytest.hookimpl(trylast=True)
def pytest_load_initial_conftests(
    early_config: pytest.Config,
    parser: pytest.Parser,
    args: list[str],
) -> None:
    """Start testcontainers early in pytest lifecycle.

    This hook runs after pytest-django configures DJANGO_SETTINGS_MODULE
    (due to trylast=True) but before any fixtures execute, ensuring
    containers are ready and settings are patched before django_db_setup.

    Args:
        early_config: The pytest config object
        parser: The pytest parser
        args: Command line arguments
    """
    global _container_manager, _original_settings

    from django.conf import settings

    if not settings.configured:
        return

    _container_manager = ContainerManager(settings)
    settings_updates = _container_manager.start_containers()

    _apply_settings_updates(settings, settings_updates)

    for provider_name in _container_manager.active_containers.keys():
        print(f"Started {provider_name} container for testing")


def pytest_unconfigure(config: pytest.Config) -> None:
    """Stop testcontainers when pytest exits.

    Args:
        config: The pytest config object
    """
    global _container_manager, _original_settings

    if _container_manager is not None:
        from django.conf import settings

        _restore_settings(settings)
        print("Stopping test containers...")
        _container_manager.stop_containers()
        _container_manager = None


@pytest.fixture(scope="session")
def testcontainers_manager() -> ContainerManager | None:
    """Get the active container manager.

    Returns:
        ContainerManager instance with active containers
    """
    return _container_manager


def _apply_settings_updates(settings: Any, updates: dict[str, Any]) -> None:
    """Apply settings updates and save originals for restoration.

    Args:
        settings: Django settings module
        updates: Dict of settings to update
    """
    global _original_settings

    for key, value in updates.items():
        if key not in _original_settings:
            _original_settings[key] = getattr(settings, key, None)

        if isinstance(value, dict) and hasattr(settings, key):
            original = getattr(settings, key, {})
            if isinstance(original, dict):
                merged = {**original, **value}
                setattr(settings, key, merged)
            else:
                setattr(settings, key, value)
        else:
            setattr(settings, key, value)


def _restore_settings(settings: Any) -> None:
    """Restore original settings values.

    Args:
        settings: Django settings module
    """
    global _original_settings

    for key, value in _original_settings.items():
        setattr(settings, key, value)
    _original_settings.clear()
