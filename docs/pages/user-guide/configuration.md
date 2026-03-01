# Configuration

Django Testcontainers Plus works with zero configuration, but you can customize every aspect of container behaviour through the `TESTCONTAINERS` setting.

## The `TESTCONTAINERS` Setting

All configuration lives under a single `TESTCONTAINERS` dict in your Django settings:

```python title="settings.py"
TESTCONTAINERS = {
    'postgres': { ... },
    'mysql':    { ... },
    'redis':    { ... },
}
```

Each key maps to a provider name. All keys are optional - omit any provider you don't need to customize.

---

## Auto-Detection

By default, every provider auto-detects whether it is needed by inspecting your Django settings. No configuration required.

| Provider | Detected from |
|---|---|
| `postgres` | `DATABASES[*]['ENGINE']` containing `postgresql` or `psycopg` |
| `mysql` | `DATABASES[*]['ENGINE']` containing `mysql` or `mariadb` |
| `redis` | `CACHES[*]['BACKEND']`, `CELERY_BROKER_URL`, `SESSION_ENGINE` |

---

## Customizing a Provider

### Change the Docker Image

```python
TESTCONTAINERS = {
    'postgres': {
        'image': 'postgres:15-alpine',
    },
    'redis': {
        'image': 'redis:7-alpine',
    },
}
```

### Override Credentials

```python
TESTCONTAINERS = {
    'postgres': {
        'username': 'myuser',
        'password': 'mypassword',
        'dbname':   'mydb',
    },
}
```

### Pass Extra Environment Variables

```python
TESTCONTAINERS = {
    'postgres': {
        'environment': {
            'POSTGRES_INITDB_ARGS': '--encoding=UTF8',
        },
    },
}
```

---

## Disabling Auto-Detection

Prevent a provider from being auto-started even when it would normally be detected:

```python
TESTCONTAINERS = {
    'redis': {
        'auto': False,
    },
}
```

---

## Explicit Enable / Disable

Force a provider on or off regardless of what's in your settings:

```python
TESTCONTAINERS = {
    # Always start a postgres container, even if not in DATABASES
    'postgres': {
        'enabled': True,
    },
    # Never start a redis container
    'redis': {
        'enabled': False,
    },
}
```

!!! note "Priority"
    `enabled` takes precedence over auto-detection. If `enabled` is set, `auto` is ignored.

---

## Full Reference

### PostgreSQL (`postgres`)

| Key | Type | Default | Description |
|---|---|---|---|
| `image` | `str` | `"postgres:16"` | Docker image to use |
| `username` | `str` | `"test"` | Database username |
| `password` | `str` | `"test"` | Database password |
| `dbname` | `str` | `"test"` | Database name |
| `environment` | `dict` | `{}` | Extra environment variables |
| `auto` | `bool` | `True` | Enable auto-detection |
| `enabled` | `bool` | _(unset)_ | Force enable/disable |

### MySQL / MariaDB (`mysql`)

| Key | Type | Default | Description |
|---|---|---|---|
| `image` | `str` | `"mysql:8"` | Docker image to use |
| `username` | `str` | `"test"` | Database username |
| `password` | `str` | `"test"` | Database password |
| `dbname` | `str` | `"test"` | Database name |
| `environment` | `dict` | `{}` | Extra environment variables |
| `auto` | `bool` | `True` | Enable auto-detection |
| `enabled` | `bool` | _(unset)_ | Force enable/disable |

### Redis (`redis`)

| Key | Type | Default | Description |
|---|---|---|---|
| `image` | `str` | `"redis:7-alpine"` | Docker image to use |
| `environment` | `dict` | `{}` | Extra environment variables |
| `auto` | `bool` | `True` | Enable auto-detection |
| `enabled` | `bool` | _(unset)_ | Force enable/disable |