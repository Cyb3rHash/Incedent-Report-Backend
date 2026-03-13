#!/usr/bin/env bash
set -euo pipefail

# Local runner for Incident Report Backend (FastAPI + Alembic + Uvicorn)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

VENV_DIR="${VENV_DIR:-.venv}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-3002}"

echo "==> Incident Report Backend local runner"
echo "    dir: ${SCRIPT_DIR}"

# -------------------------------
# Check DATABASE_URL
# -------------------------------
if [[ -z "${DATABASE_URL:-}" ]]; then
  echo "ERROR: DATABASE_URL is not set."
  echo "Example:"
  echo "export DATABASE_URL='postgresql+asyncpg://USER:PASSWORD@HOST:5432/DB?sslmode=require'"
  exit 1
fi

# -------------------------------
# Create virtual environment
# -------------------------------
if [[ ! -d "${VENV_DIR}" ]]; then
  echo "==> Creating venv: ${VENV_DIR}"
  "${PYTHON_BIN}" -m venv "${VENV_DIR}"
fi

VENV_PY="${SCRIPT_DIR}/${VENV_DIR}/bin/python"
VENV_PIP="${SCRIPT_DIR}/${VENV_DIR}/bin/pip"
VENV_ALEMBIC="${SCRIPT_DIR}/${VENV_DIR}/bin/alembic"
VENV_UVICORN="${SCRIPT_DIR}/${VENV_DIR}/bin/uvicorn"

# -------------------------------
# Upgrade pip
# -------------------------------
echo "==> Upgrading pip/setuptools/wheel"
"${VENV_PY}" -m pip install --upgrade pip setuptools wheel

# -------------------------------
# Install dependencies
# -------------------------------
if [[ "${REINSTALL:-0}" == "1" ]]; then
  echo "==> Reinstalling dependencies"
  "${VENV_PIP}" install --force-reinstall -r requirements.txt
else
  echo "==> Installing dependencies"
  "${VENV_PIP}" install -r requirements.txt
fi

# -------------------------------
# Preflight DATABASE_URL (shape + DNS)
# -------------------------------
echo "==> Validating DATABASE_URL (shape + DNS preflight)"
"${VENV_PY}" -c "from app.db.url import validate_database_url_for_runtime; import os; validate_database_url_for_runtime(os.environ.get('DATABASE_URL',''), dns_preflight=True); print('DATABASE_URL OK')"

# -------------------------------
# Run database migrations
# -------------------------------
if [[ "${SKIP_MIGRATIONS:-0}" != "1" ]]; then
  echo "==> Running migrations"
  "${VENV_ALEMBIC}" upgrade head
else
  echo "==> Skipping migrations"
fi

# -------------------------------
# Start FastAPI server
# -------------------------------
echo "==> Starting server"
echo "    URL: http://localhost:${PORT}"
echo "    Docs: http://localhost:${PORT}/docs"

exec "${VENV_UVICORN}" app.main:app --host "${HOST}" --port "${PORT}"
