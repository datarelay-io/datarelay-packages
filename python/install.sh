#!/bin/bash
# Bootstrap script for the DataRelay Python package.
# Run this once on the remote machine to install dependencies and the package.
#
# Usage:
#   bash install.sh
#   bash install.sh --upgrade   # reinstall/upgrade to latest

set -e

PACKAGE_URL="git+https://github.com/datarelay-io/datarelay-packages.git#subdirectory=python"
UPGRADE=${1:-""}

# ── Check Python ──────────────────────────────────────────────────────────────
if ! command -v python3 &>/dev/null; then
  echo "Error: python3 is not installed."
  echo "  Ubuntu/Debian: sudo apt install python3 python3-pip"
  exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(sys.version_info[:2] >= (3,10))')
if [[ "$PYTHON_VERSION" != "True" ]]; then
  echo "Error: Python 3.10+ is required (found $(python3 --version))."
  exit 1
fi

echo "✓ Python $(python3 --version | cut -d' ' -f2)"

# ── Check pip ─────────────────────────────────────────────────────────────────
if ! command -v pip3 &>/dev/null && ! python3 -m pip --version &>/dev/null; then
  echo "Error: pip is not installed."
  echo "  Ubuntu/Debian: sudo apt install python3-pip"
  exit 1
fi

PIP="python3 -m pip"
echo "✓ pip $($PIP --version | cut -d' ' -f2)"

# ── Check cryptography ────────────────────────────────────────────────────────
if python3 -c "import cryptography" &>/dev/null; then
  echo "✓ cryptography $(python3 -c 'import cryptography; print(cryptography.__version__)')"
else
  echo "Installing cryptography..."
  $PIP install --break-system-packages cryptography 2>/dev/null || \
  $PIP install cryptography
fi

# ── Install datarelay ─────────────────────────────────────────────────────────
if [[ "$UPGRADE" == "--upgrade" ]]; then
  echo "Upgrading datarelay..."
  $PIP install --break-system-packages --upgrade "$PACKAGE_URL" 2>/dev/null || \
  $PIP install --upgrade "$PACKAGE_URL"
elif python3 -c "import datarelay" &>/dev/null; then
  echo "✓ datarelay already installed"
else
  echo "Installing datarelay..."
  $PIP install --break-system-packages "$PACKAGE_URL" 2>/dev/null || \
  $PIP install "$PACKAGE_URL"
fi

echo ""
echo "✓ datarelay $(python3 -c 'import importlib.metadata; print(importlib.metadata.version(\"datarelay\"))')"
echo ""
echo "Ready. Usage:"
echo ""
echo "  from datarelay import decrypt_params"
echo "  params = decrypt_params()  # decrypts all DR_* env vars"
echo ""
