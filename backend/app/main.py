"""
Compatibility module for tests that import `from app.main import app`.

The real FastAPI app instance is defined in `backend/main.py`.
"""

from ..main import app  # type: ignore[F401]

__all__ = ["app"]
