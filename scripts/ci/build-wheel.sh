#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
OUT_DIR="${OUT_DIR:-$ROOT_DIR/dist}"
INSTALL_BUILD_DEPS=1
USE_BUILD_ISOLATION=0
CLEAN_FIRST=0
VERSION_OVERRIDE="${VERSION_OVERRIDE:-}"
REPAIR_LINUX_WHEEL=1

log() {
  printf '[build-wheel] %s\n' "$*"
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
    wheel_name = next(name for name in zf.namelist() if name.endswith('.dist-info/WHEEL'))
    metadata = Parser().parsestr(zf.read(metadata_name).decode('utf-8', errors='replace'))
    wheel_text = zf.read(wheel_name).decode('utf-8', errors='replace')

metadata_version = metadata.get('Metadata-Version', '')
dynamic_fields = metadata.get_all('Dynamic', [])
generator = ''
for line in wheel_text.splitlines():
    if line.startswith('Generator:'):
        generator = line.split(':', 1)[1].strip()
        break

print(f"Validated {wheel_path.name}")
print(f"  Metadata-Version: {metadata_version}")
print(f"  Dynamic fields: {dynamic_fields or '[]'}")
print(f"  Generator: {generator or '<unknown>'}")

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
        "Invalid wheel metadata: found Dynamic fields with Metadata-Version "
        f"{metadata_version}. Rebuild with a newer build toolchain."
    )
PY
}

wheel_needs_linux_repair() {
  "$PYTHON_BIN" - "$1" <<'PY'
import sys
import zipfile

wheel_path = sys.argv[1]
with zipfile.ZipFile(wheel_path) as zf:
    wheel_name = next(name for name in zf.namelist() if name.endswith('.dist-info/WHEEL'))
    wheel_text = zf.read(wheel_name).decode('utf-8', errors='replace')

tags = [
    line.split(':', 1)[1].strip()
    for line in wheel_text.splitlines()
    if line.startswith('Tag:')
]
needs_repair = any(tag.endswith('linux_x86_64') or 'linux_' in tag for tag in tags) and not any(
    'manylinux' in tag or 'musllinux' in tag for tag in tags
)
raise SystemExit(0 if needs_repair else 1)
PY
}

repair_linux_wheels() {
  local repair_dir
  repair_dir="$(mktemp -d)"
  local repaired_any=0
  shopt -s nullglob
  local wheels=("$OUT_DIR"/*.whl)
  shopt -u nullglob

  if [[ ${#wheels[@]} -eq 0 ]]; then
    printf 'Error: no wheels found in %s for repair\n' "$OUT_DIR" >&2
    exit 1
  fi

  require_cmd patchelf

  for wheel_file in "${wheels[@]}"; do
    if wheel_needs_linux_repair "$wheel_file"; then
      log "Repairing Linux wheel with auditwheel: $(basename "$wheel_file")"
      "$PYTHON_BIN" -m auditwheel repair --wheel-dir "$repair_dir" "$wheel_file"
      rm -f "$wheel_file"
      repaired_any=1
    fi
  done

  if [[ $repaired_any -eq 1 ]]; then
    shopt -s nullglob
    local repaired_wheels=("$repair_dir"/*.whl)
    shopt -u nullglob
    if [[ ${#repaired_wheels[@]} -eq 0 ]]; then
      printf 'Error: auditwheel repair did not produce any wheel artifacts\n' >&2
      exit 1
    fi
    mv "$repair_dir"/*.whl "$OUT_DIR"/
  fi

  rm -rf "$repair_dir"
}

usage() {
  cat <<'EOF'
Usage: scripts/ci/build-wheel.sh [options]

Options:
  --python <path>              Python executable to use
  --out-dir <path>             Wheel output directory (default: dist)
  --version <value>            Override package version for this build
  --clean                      Remove previous build outputs first
  --skip-install-build-deps    Skip installing Python build dependencies
  --use-build-isolation        Build with PEP 517 isolation enabled
  --skip-repair-linux-wheel    Skip auditwheel repair on Linux
  --help                       Show this help text

Environment variables:
  PYTHON_BIN                   Same as --python
  OUT_DIR                      Same as --out-dir
  VERSION_OVERRIDE             Same as --version
  CTX_VERSION                  Passed through to Rust CLI build
  SETUPTOOLS_SCM_PRETEND_VERSION_FOR_ATOM_CTX
                               Passed through to setuptools_scm
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
    --out-dir)
      OUT_DIR="$2"
      shift 2
      ;;
    --version)
      VERSION_OVERRIDE="$2"
      shift 2
      ;;
    --clean)
      CLEAN_FIRST=1
      shift
      ;;
    --skip-install-build-deps)
      INSTALL_BUILD_DEPS=0
      shift
      ;;
    --use-build-isolation)
      USE_BUILD_ISOLATION=1
      shift
      ;;
    --skip-repair-linux-wheel)
      REPAIR_LINUX_WHEEL=0
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
require_cmd go
require_cmd cargo
require_cmd rustc
require_cmd cmake

case "$(uname -s)" in
  MINGW*|MSYS*|CYGWIN*)
    ;;
  *)
    require_cmd make
    ;;
esac

if [[ $CLEAN_FIRST -eq 1 ]]; then
  log "Cleaning previous build outputs"
  rm -rf "$ROOT_DIR/build" "$ROOT_DIR/dist" "$OUT_DIR" "$ROOT_DIR"/*.egg-info
fi

log "Using Python: $("$PYTHON_BIN" -c 'import sys; print(sys.executable)')"
"$PYTHON_BIN" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)'

if [[ $INSTALL_BUILD_DEPS -eq 1 ]]; then
  log "Installing Python build dependencies"
  "$PYTHON_BIN" -m pip install --upgrade pip
  "$PYTHON_BIN" -m pip install --upgrade \
    "build>=1.2.2" \
    "setuptools>=61.0" \
    "setuptools-scm>=8.0" \
    "wheel>=0.45.1" \
    "cmake>=3.15"
  if [[ "$(uname -s)" == "Linux" ]]; then
    "$PYTHON_BIN" -m pip install --upgrade "auditwheel>=6.1.0"
  fi
fi

mkdir -p "$OUT_DIR"

export GOPROXY="${GOPROXY:-https://proxy.golang.org,direct}"
export GOSUMDB="${GOSUMDB:-sum.golang.org}"
export CARGO_REGISTRIES_CRATES_IO_PROTOCOL="${CARGO_REGISTRIES_CRATES_IO_PROTOCOL:-sparse}"

if [[ -n "$VERSION_OVERRIDE" ]]; then
  export CTX_VERSION="$VERSION_OVERRIDE"
  export SETUPTOOLS_SCM_PRETEND_VERSION_FOR_ATOM_CTX="$VERSION_OVERRIDE"
  log "Using version override: $VERSION_OVERRIDE"
fi

build_cmd=("$PYTHON_BIN" -m build --wheel --outdir "$OUT_DIR")
if [[ $USE_BUILD_ISOLATION -eq 0 ]]; then
  build_cmd+=(--no-isolation)
fi

log "Running: ${build_cmd[*]}"
"${build_cmd[@]}"

if [[ "$(uname -s)" == "Linux" && $REPAIR_LINUX_WHEEL -eq 1 ]]; then
  repair_linux_wheels
fi

log "Built wheel artifacts:"
ls -1 "$OUT_DIR"

for wheel_file in "$OUT_DIR"/*.whl; do
  validate_wheel_metadata "$wheel_file"
done
