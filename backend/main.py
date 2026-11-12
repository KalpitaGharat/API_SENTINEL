"""API Sentinel Backend ASGI Entrypoint for Vercel and local runtimes.

Exposes the FastAPI application instance `app` from `app.main`.
"""

import os
import sys

# Ensure backend directory is in sys.path
_backend_dir = os.path.dirname(os.path.abspath(__file__))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from app.main import app  # noqa: E402

__all__ = ["app"]
