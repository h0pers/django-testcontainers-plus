# Troubleshooting

## Missing Dependency Errors

### MySQL Support Not Installed

```
======================================================================
MySQL Support Not Installed
======================================================================

MySQL was detected in your Django settings:
  → DATABASES['default']['ENGINE']

To enable MySQL support, install the required dependencies:
  pip install django-testcontainers-plus[mysql]
======================================================================
```

**Cause:** MySQL was detected in your `DATABASES` settings, but `mysql-connector-python` is not installed.

**Fix:**
```bash
pip install django-testcontainers-plus[mysql]
```

```bash
pip install django-testcontainers-plus[all]
```

### Redis Support Not Installed

Same pattern as MySQL - install the redis extra:

```bash
pip install django-testcontainers-plus[redis]
```

---

## Common Questions

**Q: Why do I need extras for MySQL/Redis but not PostgreSQL?**

PostgreSQL works without extras because the base `testcontainers` package includes
PostgreSQL support. MySQL and Redis require their respective Python client libraries.

---

**Q: Can I disable auto-detection for a service I'm not using?**

Yes - set `auto: False` in your `TESTCONTAINERS` config:

```python
TESTCONTAINERS = {
    'redis': {
        'auto': False,
    }
}
```

---

**Q: A service was detected but I don't actually use it in tests**

Check your settings for indirect references to Redis or MySQL in:

- `DATABASES` - database engines
- `CACHES` - cache backends
- `CELERY_BROKER_URL` - Celery broker
- `SESSION_ENGINE` - session storage

Disable detection for that service with `auto: False`.

---

**Q: Tests work locally but fail in CI**

Ensure your CI environment has:

1. **Docker available** - most CI providers (GitHub Actions, GitLab CI) include it
2. **All required extras installed** - `pip install django-testcontainers-plus[all]`
3. **Sufficient Docker permissions** - some environments require `sudo` or a docker group

---

**Q: Container startup is slow**

Docker needs to pull images on first run. After that, images are cached locally.
In CI, use Docker layer caching to speed this up.

---

**Q: Port conflicts**

Containers use randomly assigned ports, so conflicts are rare. If you're seeing
connection issues, ensure no other services are binding to the same port range.

---

## Getting Help

If you can't find your answer here, please [open an issue](https://github.com/WoodyWoodster/django-testcontainers-plus/issues) on GitHub with:

- Your `DATABASES` / `CACHES` settings (redact sensitive values)
- The full error traceback
- Your Python, Django, and package versions