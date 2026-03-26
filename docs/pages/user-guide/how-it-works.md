# How It Works

Django Testcontainers Plus follows a simple lifecycle every time you run tests.

## Lifecycle Overview

```
Test run starts
      │
      ▼
  1. Detection
     Scan Django settings for known service patterns
     (DATABASES engines, CACHES backends, CELERY_BROKER_URL, etc.)
      │
      ▼
  2. Configuration
     Merge detected needs with TESTCONTAINERS setting overrides
      │
      ▼
  3. Startup
     Start Docker containers for each needed service
      │
      ▼
  4. Injection
     Patch Django settings with container host/port/credentials
      │
      ▼
  5. Your tests run against real services
      │
      ▼
  6. Teardown
     Stop and remove all containers, restore original settings
```

## Step-by-Step

### 1. Detection

The `ContainerManager` iterates over all registered providers and asks each one:
_"Are you needed based on these Django settings?"_

Each provider implements `can_auto_detect()` which inspects specific settings keys:

- **PostgreSQL**: checks `DATABASES[*]['ENGINE']` for `postgresql` or `psycopg`
- **MySQL**: checks `DATABASES[*]['ENGINE']` for `mysql` or `mariadb`
- **Redis**: checks `CACHES[*]['BACKEND']`, `CELERY_BROKER_URL`, and `SESSION_ENGINE`

### 2. Configuration

Detected providers are merged with any overrides from the `TESTCONTAINERS` setting.
Your overrides always win over provider defaults.

You can also explicitly enable a provider via `enabled: True` (skipping auto-detection)
or suppress one via `auto: False` or `enabled: False`.

### 3. Startup

For each needed provider, the manager:

1. Calls `provider.get_container(config)` to create a configured `DockerContainer`
2. Calls `container.start()` - Docker pulls the image if needed and starts the container
3. Waits for the container to be ready (health-checked by the `testcontainers` library)

### 4. Injection

Each started container exposes its host IP and mapped port. The provider's
`update_settings()` method builds a patch dict, for example:

```python
{
    "DATABASES": {
        "default": {
            "HOST": "localhost",
            "PORT": "54321",  # randomly assigned by Docker
            "USER": "test",
            "PASSWORD": "test",
            "NAME": "test",
        }
    }
}
```

These patches are applied directly to Django's live settings object, so all
subsequent database connections use the container automatically.

### 5. Test Execution

Your tests run normally against real PostgreSQL, MySQL, or Redis instances in Docker -
no mocks, no fakes.

### 6. Teardown

After all tests complete:

1. Original Django settings are restored
2. Each container is stopped and removed via `container.stop()`
3. Docker cleans up the network and volumes

## Integration Points

### Django Test Runner

`TestcontainersRunner` extends Django's `DiscoverRunner`. It hooks into
`setup_test_environment()` to start containers before the test database is created,
and `teardown_test_environment()` to stop them after.

### pytest Plugin

The pytest plugin overrides pytest-django's `django_db_setup` fixture at `session`
scope. Containers start once per test session before any database setup, and are
torn down after all tests complete.