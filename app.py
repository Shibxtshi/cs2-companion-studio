"""Compatibility entry point for uvicorn app:app and existing Python callers."""
import sys

from companion import server as _server

# Keep one module/state object, including callers that patch app attributes.
sys.modules[__name__] = _server
