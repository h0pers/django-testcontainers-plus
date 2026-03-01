# API Reference

This section documents the public API of Django Testcontainers Plus.

## Modules

| Module | Description |
|---|---|
| `django_testcontainers_plus.runner` | Django test runner integration |
| `django_testcontainers_plus.pytest_plugin` | pytest fixtures |
| `django_testcontainers_plus.manager` | Container lifecycle management |
| `django_testcontainers_plus.providers` | Container provider implementations |
| `django_testcontainers_plus.exceptions` | Custom exception classes |

## Key Classes

### TestcontainersRunner

The Django test runner that automatically manages containers.

**Import path:** `django_testcontainers_plus.runner.TestcontainersRunner`

**Usage:**
```python
# settings.py
TEST_RUNNER = 'django_testcontainers_plus.runner.TestcontainersRunner'
```

### ContainerManager

Manages the full lifecycle of test containers - detection, startup, settings injection, and teardown.

**Import path:** `django_testcontainers_plus.manager.ContainerManager`

### ContainerProvider

Abstract base class for all container providers. Implement this to add support for a new service.

**Import path:** `django_testcontainers_plus.providers.base.ContainerProvider`

## pytest Fixtures

| Fixture | Scope | Description |
|---|---|---|
| `django_db_setup` | `session` | Overrides pytest-django's setup to start containers first |
| `testcontainers_manager` | `session` | Returns the active `ContainerManager` instance |

## Exceptions

| Exception | Description |
|---|---|
| `DjangoTestcontainersError` | Base exception for all library errors |
| `MissingDependencyError` | Raised when a required extra is not installed |