"""Opt-in unit tests when PostgreSQL is unavailable; normal settings use PostgreSQL."""
from .settings import *  # noqa: F403

DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}
