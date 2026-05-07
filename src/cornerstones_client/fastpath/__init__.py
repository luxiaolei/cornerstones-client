"""Lightweight read-only fast path for the core ``cornerstones`` CLI.

This package must stay import-cheap: no Cornerstones core domain/API/provider imports.
"""

from .runner import run

__all__ = ["run"]
