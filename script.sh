#!/usr/bin/env bash
set -euo pipefail

# Backend-only runner for Incident Report Backend (FastAPI + Uvicorn)
#
# Purpose:
#   - Start the FastAPI server for preview use.
#   - Do NOT perform any DB validation or migrations (user will connect/configure DB separately).
#
# Preview binding contract:
#   - Must listen on 0.0.0.0:3002 so the preview system can connect.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

VENV_DIR="${VENV_DIR:-.venv}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

# Preview system expects these defaults; do not depend on DATABASE_URL or any DB steps.
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-3002}"

echo "==> Incident Report Backend (backend-only runner)"
echo "    dir: ${SCRIPT_DIR}"
echo "    host: ${HOST}"
echo "    port: ${PORT}"

# -------------------------------
# Create virtual environment
# -------------------------------
if [[ ! -d "${VENV_DIR}" ]]; then
  echo "==> Creating venv: ${VENV_DIR}"
  "${PYTHON_BIN}" -m venv "${VENV_DIR}"
fi

VENV_PY="${SCRIPT_DIR}/${VENV_DIR}/bin/python"
VENV_PIP="${SCRIPT_DIR}/${VENV_DIR}/bin/pip"
VENV_UVICORN="${SCRIPT_DIR}/${VENV_DIR}/bin/uvicorn"

# -------------------------------
# Install dependencies
# -------------------------------
# Keep this lightweight and non-interactive; no DB calls.
if [[ "${REINSTALL:-0}" == "1" ]]; then
  echo "==> Reinstalling dependencies"
  "${VENV_PIP}" install --force-reinstall -r requirements.txt
else
  echo "==> Installing dependencies"
  "${VENV_PIP}" install -r requirements.txt
fi

# -------------------------------
# Start FastAPI server
# -------------------------------
echo "==> Starting server"
echo "    URL:  http://localhost:${PORT}"
echo "    Docs: http://localhost:${PORT}/docs"

exec "${VENV_UVICORN}" app.main:app --host "${HOST}" --port "${PORT}"
