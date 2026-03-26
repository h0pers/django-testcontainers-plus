"""Shared test helpers."""


class MockSettings:
    """Mock Django settings object for testing."""

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
