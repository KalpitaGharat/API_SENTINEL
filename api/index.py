"""Vercel Serverless Function entrypoint for API Sentinel FastAPI Backend.

Provides serverless ASGI compatibility for Vercel deployment.
"""

import os
import sys

# Ensure backend root is on sys.path so 'app.*' imports resolve cleanly
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.abspath(os.path.join(current_dir, "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.main import app  # noqa: E402
