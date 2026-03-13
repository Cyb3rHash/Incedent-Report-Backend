from __future__ import annotations

from dataclasses import dataclass
import socket
from typing import Any, Dict, MutableMapping, Optional
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


@dataclass(frozen=True)
class NormalizedDatabaseConfig:
    """Normalized DB config for SQLAlchemy asyncpg.

    Contract:
      Inputs:
        - raw_url: Database URL (may be postgres://, postgresql://, or postgresql+asyncpg://)
          and may include SSL-related query params like sslmode=require (common for Neon).
      Outputs:
        - sqlalchemy_url: URL safe to pass to SQLAlchemy create_async_engine() with asyncpg.
          Invariant: contains no `sslmode` query parameter (asyncpg does not accept it).
        - connect_args: Dict to pass as SQLAlchemy create_async_engine(connect_args=...).
          Invariant: if SSL is required by URL params, connect_args includes {"ssl": "require"}.
      Errors:
        - ValueError if raw_url is empty/blank, or if the URL is clearly misconfigured.
      Side effects:
        - None (pure transformation).
    """

    sqlalchemy_url: str
    connect_args: Dict[str, Any]


def _extract_hostname(url: str) -> str | None:
    """Extract hostname from a DB URL, returning None if it cannot be parsed."""
    parts = urlsplit(url)
    # urlsplit() provides hostname parsing that handles userinfo/port properly.
    return parts.hostname


def _looks_like_bad_hostname(hostname: str) -> bool:
    """Heuristics for common misconfigurations where hostname is not a hostname.

    Examples caught:
      - hostname contains a scheme ("https://...")
      - hostname contains '/' (copied full URL/path)
      - hostname is wrapped in quotes
    """
    h = hostname.strip().strip("'").strip('"')
    return ("://" in h) or ("/" in h) or (h == "")


# PUBLIC_INTERFACE
def validate_database_url_for_runtime(raw_url: str, *, dns_preflight: bool = True) -> None:
    """Validate DATABASE_URL and surface actionable errors early.

    This is a *boundary* validation used by:
      - Alembic migrations (so failures are clear before attempting a connection)
      - Local runner scripts (fail fast before running alembic)
      - Potential future startup checks

    Contract:
      Inputs:
        - raw_url: str from environment variable DATABASE_URL.
        - dns_preflight: if True, attempts to resolve the hostname via getaddrinfo.
      Outputs:
        - None (returns normally if valid enough to attempt a connection).
      Errors:
        - ValueError with an actionable message when invalid/misconfigured.
      Side effects:
        - DNS lookup when dns_preflight=True.

    Notes:
      - This does NOT attempt to authenticate or connect to Postgres; it only validates
        that the URL is parseable and the hostname is resolvable.
    """
    if not raw_url or not raw_url.strip():
        raise ValueError(
            "DATABASE_URL is empty. Set it to your Neon Postgres connection string, e.g. "
            "'postgresql://USER:PASSWORD@HOST:5432/DB?sslmode=require'."
        )

    url = raw_url.strip()
    hostname = _extract_hostname(url)
    if not hostname:
        raise ValueError(
            "DATABASE_URL is missing a hostname. Ensure it looks like "
            "'postgresql://USER:PASSWORD@HOST:5432/DB?sslmode=require'."
        )

    if _looks_like_bad_hostname(hostname):
        raise ValueError(
            f"DATABASE_URL hostname looks invalid: {hostname!r}. "
            "Common mistake: pasting a full URL (with https://) or a full `psql ...` command "
            "instead of just the Postgres connection string."
        )

    if dns_preflight:
        try:
            # Use default service/port resolution; we only care whether the name resolves.
            socket.getaddrinfo(hostname, None)
        except socket.gaierror as e:
            raise ValueError(
                f"Cannot resolve DATABASE_URL host {hostname!r} (DNS lookup failed). "
                "Verify the Neon host is correct and reachable from this environment. "
                "If you copied from Neon dashboard, ensure no extra quotes/spaces were included."
            ) from e


def _normalize_scheme_to_asyncpg(url: str) -> str:
    """Normalize Postgres URL schemes to SQLAlchemy asyncpg driver URLs."""
    if url.startswith("postgresql+asyncpg://"):
        return url
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    return url


def _pop_query_param(
    query_params: MutableMapping[str, str], key: str
) -> Optional[str]:
    """Pop a query param key (case-insensitive) from query_params."""
    for k in list(query_params.keys()):
        if k.lower() == key.lower():
            return query_params.pop(k)
    return None


# PUBLIC_INTERFACE
def normalize_asyncpg_database_url(raw_url: str) -> NormalizedDatabaseConfig:
    """Normalize a database URL for SQLAlchemy asyncpg and Neon SSL requirements.

    Why:
      - Neon commonly provides connection strings like:
          postgresql://.../db?sslmode=require
      - With SQLAlchemy + asyncpg, URL query params are forwarded as connect kwargs to
        asyncpg.connect(). asyncpg does NOT accept 'sslmode', causing:
          TypeError: connect() got an unexpected keyword argument 'sslmode'
      - A misconfigured hostname otherwise fails later as:
          socket.gaierror: [Errno -5] No address associated with hostname

    What this does:
      1) Validates DATABASE_URL shape and (by default) performs a DNS preflight for the host.
      2) Normalizes postgres/postgresql scheme to postgresql+asyncpg.
      3) Removes `sslmode` from the URL query string so it isn't forwarded to asyncpg.
      4) Maps sslmode requirement to SQLAlchemy connect_args:
           sslmode=require|verify-ca|verify-full  -> connect_args["ssl"] = "require"
         (This is sufficient for Neon, which requires TLS.)

    Args:
      raw_url: Database URL from environment.

    Returns:
      NormalizedDatabaseConfig with sqlalchemy_url and connect_args.
    """
    validate_database_url_for_runtime(raw_url, dns_preflight=True)
    url = _normalize_scheme_to_asyncpg(raw_url.strip())

    parts = urlsplit(url)
    query_pairs = parse_qsl(parts.query, keep_blank_values=True)

    # Use a dict for manipulation, but preserve "last one wins" semantics.
    query: Dict[str, str] = {}
    for k, v in query_pairs:
        query[k] = v

    sslmode = _pop_query_param(query, "sslmode")
    ssl = _pop_query_param(query, "ssl")  # some providers use ssl=true

    connect_args: Dict[str, Any] = {}

    ssl_required = False
    if sslmode:
        sslmode_norm = sslmode.strip().lower()
        if sslmode_norm in {"require", "verify-ca", "verify-full"}:
            ssl_required = True
        # If sslmode is "disable"/unknown, we don't force TLS.
    if ssl:
        ssl_norm = ssl.strip().lower()
        if ssl_norm in {"1", "true", "yes", "on", "require"}:
            ssl_required = True

    if ssl_required:
        # asyncpg accepts an ssl context or True-ish values.
        # SQLAlchemy dialect accepts 'connect_args' and passes through.
        connect_args["ssl"] = "require"

    new_query = urlencode(list(query.items()))
    normalized_url = urlunsplit((parts.scheme, parts.netloc, parts.path, new_query, parts.fragment))
    return NormalizedDatabaseConfig(sqlalchemy_url=normalized_url, connect_args=connect_args)
