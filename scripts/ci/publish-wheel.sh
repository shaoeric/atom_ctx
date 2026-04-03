#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
DIST_DIR="${DIST_DIR:-$ROOT_DIR/dist}"
REPOSITORY="${REPOSITORY:-pypi}"
REPOSITORY_URL="${REPOSITORY_URL:-}"
SKIP_EXISTING=1
INSTALL_PUBLISH_DEPS=1

log() {
  printf '[publish-wheel] %s\n' "$*"
}

validate_wheel_metadata() {
  "$PYTHON_BIN" - "$1" <<'PY'
import sys
import zipfile
from email.parser import Parser
from pathlib import Path

wheel_path = Path(sys.argv[1])
with zipfile.ZipFile(wheel_path) as zf:
    metadata_name = next(name for name in zf.namelist() if name.endswith('.dist-info/METADATA'))
    metadata = Parser().parsestr(zf.read(metadata_name).decode('utf-8', errors='replace'))

metadata_version = metadata.get('Metadata-Version', '')
dynamic_fields = metadata.get_all('Dynamic', [])

version_parts = []
for part in metadata_version.split('.'):
    try:
        version_parts.append(int(part))
    except ValueError:
        version_parts.append(0)

while len(version_parts) < 2:
    version_parts.append(0)

if dynamic_fields and tuple(version_parts[:2]) < (2, 2):
    raise SystemExit(
        f"{wheel_path.name}: invalid metadata for PyPI upload "
        f"(Metadata-Version {metadata_version}, Dynamic={dynamic_fields})"
    )
PY
}

validate_wheel_platform_tag() {
  "$PYTHON_BIN" - "$1" <<'PY'
import sys
import zipfile
from pathlib import Path

wheel_path = Path(sys.argv[1])
with zipfile.ZipFile(wheel_path) as zf:
    wheel_name = next(name for name in zf.namelist() if name.endswith('.dist-info/WHEEL'))
    wheel_text = zf.read(wheel_name).decode('utf-8', errors='replace')

tags = [
    line.split(':', 1)[1].strip()
    for line in wheel_text.splitlines()
    if line.startswith('Tag:')
]

unsupported = [
    tag for tag in tags
    if 'linux_' in tag and 'manylinux' not in tag and 'musllinux' not in tag
]
if unsupported:
    raise SystemExit(
        f"{wheel_path.name}: unsupported PyPI Linux platform tag(s): {unsupported}. "
        "Run auditwheel repair before uploading."
    )
PY
}

usage() {
  cat <<'EOF'
Usage: scripts/ci/publish-wheel.sh [options]

Options:
  --python <path>              Python executable to use
  --dist-dir <path>            Directory containing wheel artifacts
  --repository <name>          Repository alias: pypi or testpypi
  --repository-url <url>       Explicit upload endpoint
  --no-skip-existing           Do not pass --skip-existing to twine
  --skip-install-publish-deps  Skip installing twine
  --help                       Show this help text

Required environment variables:
  TWINE_USERNAME               Usually __token__
  TWINE_PASSWORD               PyPI or TestPyPI API token
EOF
}

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    printf 'Error: required command not found: %s\n' "$1" >&2
    exit 1
  fi
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --python)
      PYTHON_BIN="$2"
      shift 2
      ;;
    --dist-dir)
      DIST_DIR="$2"
      shift 2
      ;;
    --repository)
      REPOSITORY="$2"
      shift 2
      ;;
    --repository-url)
      REPOSITORY_URL="$2"
      shift 2
      ;;
    --no-skip-existing)
      SKIP_EXISTING=0
      shift
      ;;
    --skip-install-publish-deps)
      INSTALL_PUBLISH_DEPS=0
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      printf 'Error: unknown argument: %s\n\n' "$1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

cd "$ROOT_DIR"

require_cmd "$PYTHON_BIN"

if [[ ! -d "$DIST_DIR" ]]; then
  printf 'Error: dist directory not found: %s\n' "$DIST_DIR" >&2
  exit 1
fi

shopt -s nullglob
artifacts=("$DIST_DIR"/*.whl)
shopt -u nullglob
if [[ ${#artifacts[@]} -eq 0 ]]; then
  printf 'Error: no wheel artifacts found in %s\n' "$DIST_DIR" >&2
  exit 1
fi

if [[ -z "${TWINE_USERNAME:-}" || -z "${TWINE_PASSWORD:-}" ]]; then
  printf 'Error: TWINE_USERNAME and TWINE_PASSWORD must be set\n' >&2
  exit 1
fi

if [[ $INSTALL_PUBLISH_DEPS -eq 1 ]]; then
  log "Installing publish dependencies"
  "$PYTHON_BIN" -m pip install --upgrade "twine>=6.1.0"
fi

for wheel_file in "${artifacts[@]}"; do
  validate_wheel_metadata "$wheel_file"
  validate_wheel_platform_tag "$wheel_file"
done

log "Validating distribution metadata"
"$PYTHON_BIN" -m twine check "$DIST_DIR"/*

upload_cmd=("$PYTHON_BIN" -m twine upload)
if [[ -n "$REPOSITORY_URL" ]]; then
  upload_cmd+=(--repository-url "$REPOSITORY_URL")
else
  upload_cmd+=(--repository "$REPOSITORY")
fi
if [[ $SKIP_EXISTING -eq 1 ]]; then
  upload_cmd+=(--skip-existing)
fi
upload_cmd+=("$DIST_DIR"/*.whl)

log "Uploading wheel artifacts"
"${upload_cmd[@]}"
