#!/usr/bin/env bash
set -euo pipefail

# Simple local runner for the Incident Report Backend (FastAPI + Alembic + Uvicorn).
#
# What it does:
#  1) Creates/uses a local Python virtualenv in .venv
#  2) Installs pip deps from requirements.txt
#  3) Runs alembic migrations via module invocation (python -m alembic upgrade head)
#     This avoids "alembic: command not found" when the venv isn't on PATH.
#  4) Starts uvicorn (app.main:app)
#
# Prereqs:
#  - Python 3 installed
#  - DATABASE_URL env var set (see .env.example / README)
#
# Usage:
#  chmod +x ./script.sh
#  ./script.sh
#
# Optional env vars:
#  HOST (default 0.0.0.0)
#  PORT (default 3002)
#  LOG_LEVEL (default INFO; used by app)
#  SKIP_MIGRATIONS=1 (skip alembic upgrade head)
#  REINSTALL=1 (force reinstall deps)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

VENV_DIR="${VENV_DIR:-.venv}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-3002}"

echo "==> Incident Report Backend local runner"
echo "    dir: ${SCRIPT_DIR}"

if [[ -z "${DATABASE_URL:-}" ]]; then
  echo "ERROR: DATABASE_URL is not set."
  echo "Set it to your Postgres connection string, e.g.:"
  echo "  export DATABASE_URL='postgresql+asyncpg://USER:PASSWORD@HOST:5432/DB?sslmode=require'"
  exit 1
fi

if [[ ! -d "${VENV_DIR}" ]]; then
  echo "==> Creating venv: ${VENV_DIR}"
  "${PYTHON_BIN}" -m venv "${VENV_DIR}"
fi

VENV_PY="${SCRIPT_DIR}/${VENV_DIR}/bin/python"
VENV_PIP="${SCRIPT_DIR}/${VENV_DIR}/bin/pip"
VENV_UVICORN="${SCRIPT_DIR}/${VENV_DIR}/bin/uvicorn"

echo "==> Upgrading pip/setuptools/wheel"
"${VENV_PY}" -m pip install --upgrade pip setuptools wheel

if [[ "${REINSTALL:-0}" == "1" ]]; then
  echo "==> Reinstall requested (REINSTALL=1). Installing requirements with --force-reinstall"
  "${VENV_PIP}" install --force-reinstall -r requirements.txt
else
  echo "==> Installing requirements"
  "${VENV_PIP}" install -r requirements.txt
fi

if [[ "${SKIP_MIGRATIONS:-0}" != "1" ]]; then
  echo "==> Running migrations: ${VENV_PY} -m alembic upgrade head"
  "${VENV_PY}" -m alembic upgrade head
else
  echo "==> Skipping migrations (SKIP_MIGRATIONS=1)"
fi

echo "==> Starting server: uvicorn app.main:app --host ${HOST} --port ${PORT}"
echo "    OpenAPI docs: http://localhost:${PORT}/docs"
exec "${VENV_UVICORN}" app.main:app --host "${HOST}" --port "${PORT}"
