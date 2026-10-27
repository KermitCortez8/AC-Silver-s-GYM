#!/usr/bin/env bash
set -euo pipefail

speckit_root="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
speckit_python="${SPECKIT_PYTHON:-python3}"

"$speckit_python" -c 'import sys; assert sys.version_info >= (3, 11), "Spec Kit requiere Python 3.11 o superior"'
"$speckit_python" -m venv "$speckit_root/.tools/spec-kit"
# Reinstalar evita conservar otro commit que declare la misma versión de la CLI.
"$speckit_root/.tools/spec-kit/bin/python" -m pip install --force-reinstall --disable-pip-version-check \
  -r "$speckit_root/tools/spec-kit-requirements.txt"
"$speckit_root/.tools/spec-kit/bin/specify" version
