# MySQL / MariaDB Provider

The MySQL provider requires the `[mysql]` extra to be installed.

## Installation

```bash
pip install django-testcontainers-plus[mysql]
```

## Auto-Detection

The provider activates automatically when any entry in `DATABASES` uses a MySQL or MariaDB engine:

| Engine string | Detected |
|---|---|
| `django.db.backends.mysql` | Yes |
| Any engine containing `mysql` | Yes |
| Any engine containing `mariadb` | Yes |

## Minimal Setup

```python title="settings.py"
TEST_RUNNER = 'django_testcontainers_plus.runner.TestcontainersRunner'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'myapp',
    }
}
```

## Default Container

| Property | Value |
|---|---|
| Image | `mysql:8` |
| Username | `test` |
| Password | `test` |
| Database | `test` |
| Port | Randomly assigned by Docker |

## Configuration Options

```python title="settings.py"
TESTCONTAINERS = {
    'mysql': {
        'image':    'mysql:8.0',
        'username': 'myuser',
        'password': 'mysecret',
        'dbname':   'myapp_test',
        'environment': {
            'MYSQL_ROOT_PASSWORD': 'rootpass',
        },
    }
}
```

## MariaDB

Use a MariaDB image to test against MariaDB:

```python title="settings.py"
TESTCONTAINERS = {
    'mysql': {
        'image': 'mariadb:11',
    }
}

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'myapp',
    }
}
```

!!! warning "Missing dependency error"
    If you see a `MySQL Support Not Installed` error, you need to install the extra:

    ```bash
    pip install django-testcontainers-plus[mysql]
    ```