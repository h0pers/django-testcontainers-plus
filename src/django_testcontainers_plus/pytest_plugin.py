from collections.abc import Generator
from typing import Any

import pytest
from django.conf import settings
from django.db import connections

from .manager import ContainerManager

_container_manager: ContainerManager | None = None
_original_settings: dict[str, Any] = {}


@pytest.fixture(scope="session")
def django_db_setup(
    request: pytest.FixtureRequest,
    django_test_environment: Any,
    django_db_blocker: Any,
    django_db_use_migrations: bool,
    django_db_keepdb: bool,
    django_db_createdb: bool,
    django_db_modify_db_settings: None,
) -> Generator[None, None, None]:
    """Override pytest-django's django_db_setup to start containers first.

    This fixture:
    1. Starts testcontainers before database setup
    2. Clears Django's connection cache to pick up new settings
    3. Reconfigures database connections with container settings
    4. Sets up the test database using pytest-django's logic
    5. Cleans up containers after all tests complete
    """
    global _container_manager, _original_settings

    # Start containers and get settings updates
    _container_manager = ContainerManager(settings)
    settings_updates = _container_manager.start_containers()

    if settings_updates:
        # Apply settings updates
        _apply_settings_updates(settings_updates)

        # Clear Django's cached connection settings
        if "settings" in connections.__dict__:
            del connections.__dict__["settings"]

        # Reconfigure connections with updated settings
        connections._settings = connections.configure_settings(settings.DATABASES)  # type: ignore[attr-defined]

        # Close all existing connections
        connections.close_all()

        # Explicitly recreate connections with new settings
        for alias in settings.DATABASES:
            connections[alias] = connections.create_connection(alias)

    # Now run pytest-django's database setup logic
    from django.test.utils import setup_databases, teardown_databases

    with django_db_blocker.unblock():
        db_cfg = setup_databases(
            verbosity=request.config.option.verbose,
            interactive=False,
            keepdb=django_db_keepdb,
            debug_sql=getattr(request.config.option, "debug_sql", False),
            parallel=0,
            aliases=None,
            serialized_aliases=None,
            run_migrations=django_db_use_migrations,
        )

    yield

    # Teardown
    with django_db_blocker.unblock():
        try:
            teardown_databases(db_cfg, verbosity=request.config.option.verbose)
        except Exception:
            pass

    if _container_manager is not None:
        _restore_settings()
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


def _apply_settings_updates(updates: dict[str, Any]) -> None:
    """Apply settings updates and save originals for restoration.

    Args:
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


def _restore_settings() -> None:
    """Restore original settings values."""
    global _original_settings

    for key, value in _original_settings.items():
        setattr(settings, key, value)
    _original_settings.clear()


pytest_plugins = ["django_testcontainers_plus.pytest_plugin"]
