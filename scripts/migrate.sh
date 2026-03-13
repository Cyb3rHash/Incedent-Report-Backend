#!/usr/bin/env bash
set -euo pipefail

# Run Alembic migrations using the *virtualenv-installed* console script.
# This avoids `python -m alembic ...`, which fails because Alembic has no `alembic.__main__`.
#
# Contract:
#   Inputs:
#     - DATABASE_URL in environment (required by alembic/env.py via app Settings).
#     - Optional VENV_DIR (default: .venv)
#     - Optional PYTHON_BIN (default: python3) used only to create venv if missing.
#     - Optional ALEMBIC_ARGS (default: "upgrade head")
#   Outputs:
#     - Exit code 0 on success, non-zero on failure.
#   Errors:
#     - Exits with actionable message if DATABASE_URL is missing or venv/alembic is not available.
#   Side effects:
#     - May create a virtualenv directory if missing.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"
cd "${SCRIPT_DIR}"

VENV_DIR="${VENV_DIR:-.venv}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
ALEMBIC_ARGS="${ALEMBIC_ARGS:-upgrade head}"

if [[ -z "${DATABASE_URL:-}" ]]; then
  echo "ERROR: DATABASE_URL is not set."
  echo "Example:"
  echo "export DATABASE_URL='postgresql+asyncpg://USER:PASSWORD@HOST:5432/DB?sslmode=require'"
  exit 1
fi

if [[ ! -d "${VENV_DIR}" ]]; then
  echo "==> Creating venv: ${VENV_DIR}"
  "${PYTHON_BIN}" -m venv "${VENV_DIR}"
fi

VENV_ALEMBIC="${SCRIPT_DIR}/${VENV_DIR}/bin/alembic"
VENV_PY="${SCRIPT_DIR}/${VENV_DIR}/bin/python"
VENV_PIP="${SCRIPT_DIR}/${VENV_DIR}/bin/pip"

if [[ ! -x "${VENV_ALEMBIC}" ]]; then
  echo "==> Installing dependencies (to ensure Alembic console script exists)"
  "${VENV_PY}" -m pip install --upgrade pip setuptools wheel
  "${VENV_PIP}" install -r requirements.txt
fi

if [[ ! -x "${VENV_ALEMBIC}" ]]; then
  echo "ERROR: Alembic console script not found at: ${VENV_ALEMBIC}"
  echo "Try: ${VENV_PIP} install -r requirements.txt"
  exit 1
fi

echo "==> Running migrations via: ${VENV_ALEMBIC} ${ALEMBIC_ARGS}"
exec "${VENV_ALEMBIC}" ${ALEMBIC_ARGS}
