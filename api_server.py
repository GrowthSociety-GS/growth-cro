#!/usr/bin/env python3
"""Shim — forwards to growthcro.api.server (will be removed in #10)."""
from growthcro.api.server import app  # noqa: F401

if __name__ == "__main__":
    import uvicorn

    from growthcro.config import config

    uvicorn.run(app, host="0.0.0.0", port=config.port(default=8000))
