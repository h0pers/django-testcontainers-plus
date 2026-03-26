# PostgreSQL Provider

The PostgreSQL provider is included by default - no extras required.

## Auto-Detection

The provider activates automatically when any entry in `DATABASES` uses a PostgreSQL engine:

| Engine string | Detected |
|---|---|
| `django.db.backends.postgresql` | Yes |
| `django.db.backends.postgresql_psycopg2` | Yes |
| Any engine containing `psycopg` | Yes |
| `django.contrib.gis.db.backends.postgis` | Not yet (see [#15](https://github.com/WoodyWoodster/django-testcontainers-plus/issues/15)) |

## Minimal Setup

```python title="settings.py"
TEST_RUNNER = 'django_testcontainers_plus.runner.TestcontainersRunner'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'myapp',
    }
}
```

No host, port, user, or password needed - they're injected automatically.

## Default Container

| Property | Value |
|---|---|
| Image | `postgres:16` |
| Username | `test` |
| Password | `test` |
| Database | `test` |
| Port | Randomly assigned by Docker |

## Configuration Options

```python title="settings.py"
TESTCONTAINERS = {
    'postgres': {
        'image':    'postgres:15-alpine',
        'username': 'myuser',
        'password': 'mysecret',
        'dbname':   'myapp_test',
        'environment': {
            'POSTGRES_INITDB_ARGS': '--encoding=UTF8 --locale=en_US.UTF-8',
        },
    }
}
```

## Multiple Databases

If your project has multiple PostgreSQL databases, all of them are updated:

```python title="settings.py"
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'primary',
    },
    'analytics': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'analytics',
    },
}
```

Both `default` and `analytics` connections will point to the same container.

## PostGIS

PostGIS is not yet auto-detected. Use `enabled: True` to start the container explicitly and provide the PostGIS image:

```python title="settings.py"
TESTCONTAINERS = {
    'postgres': {
        'enabled': True,
        'image': 'postgis/postgis:16-3.4',
    }
}

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'myapp',
    }
}
```