# Quick Start

Get up and running in under 5 minutes.

## Option 1: Django Test Runner

The simplest setup - one line in `settings.py`.

**Step 1:** Set the custom test runner:

```python title="settings.py"
TEST_RUNNER = 'django_testcontainers_plus.runner.TestcontainersRunner'
```

**Step 2:** Configure your database as normal (no host/port needed):

```python title="settings.py"
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'myapp',
    }
}
```

**Step 3:** Run your tests:

```bash
python manage.py test
```

That's it! A PostgreSQL container starts automatically, your tests run against it, and it's cleaned up when done.

---

## Option 2: pytest

**Step 1:** Register the pytest plugin in your `conftest.py`:

```python title="conftest.py"
pytest_plugins = ['django_testcontainers_plus.pytest_plugin']
```

**Step 2:** Configure your database in settings:

```python title="settings.py"
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'test',
    }
}
```

**Step 3:** Run pytest:

```bash
pytest
```

---

## Multiple Services

Both the Django runner and pytest support multiple containers simultaneously.
Just configure your services as you normally would - they'll all be auto-detected:

```python title="settings.py"
TEST_RUNNER = 'django_testcontainers_plus.runner.TestcontainersRunner'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'test',
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://localhost:6379/0',
    }
}
```

Both a **PostgreSQL** and a **Redis** container start automatically before your tests.

!!! note "Redis extra required"
    To use Redis, install the redis extra: `pip install django-testcontainers-plus[redis]`

---

## What Happens Behind the Scenes

1. Django Testcontainers Plus scans your settings for known service patterns
2. Matched containers are started via Docker
3. Django's connection settings are updated with the container's host and port
4. Tests run against real services
5. All containers are stopped and removed after tests complete

See [How It Works](../user-guide/how-it-works.md) for a deeper explanation.