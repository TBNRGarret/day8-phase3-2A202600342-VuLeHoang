#!/usr/bin/env bash
set -euo pipefail

python -m venv .venv
# shellcheck disable=SC1091
. .venv/bin/activate
python -m pip install --upgrade pip
if [ "${1-}" = "sqlite" ]; then
  python -m pip install -e ".[sqlite]"
else
  python -m pip install -e .
fi
