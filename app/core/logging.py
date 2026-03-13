from __future__ import annotations

import logging


# PUBLIC_INTERFACE
def configure_logging(log_level: str) -> None:
    """Configure application-wide logging.

    Contract:
      - Sets up basic logging formatting appropriate for container logs.
      - Safe to call once at startup.

    Args:
      log_level: Python logging level name (e.g., INFO, DEBUG).
    """
    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s :: %(message)s",
    )
