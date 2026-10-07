#!/usr/bin/env bash
# Install host packages and the project Python environment.
# Safe to re-run. Does not install NVIDIA drivers (RunPod GPU images already have them).

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

install_apt_packages() {
  if ! command -v apt-get >/dev/null 2>&1; then
    return 0
  fi
  local runner=()
  if [[ "$(id -u)" -ne 0 ]]; then
    if ! command -v sudo >/dev/null 2>&1; then
      echo "apt-get is available but this user cannot use sudo; skipping system packages."
      return 0
    fi
    runner=(sudo)
  fi
  "${runner[@]}" apt-get update
  "${runner[@]}" apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    git \
    build-essential
}

install_uv() {
  if command -v uv >/dev/null 2>&1; then
    return 0
  fi
  echo "Installing uv..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="${HOME}/.local/bin:${PATH}"
  if ! command -v uv >/dev/null 2>&1; then
    echo "uv was installed but is not on PATH. Add ${HOME}/.local/bin to PATH and re-run." >&2
    exit 1
  fi
}

install_apt_packages
install_uv

uv venv --python 3.11
uv pip install -e .
uv pip install graphrag surya-ocr python-dotenv pyarrow

if [[ ! -f "${ROOT}/.env" ]]; then
  cp "${ROOT}/.env.example" "${ROOT}/.env"
  echo "Wrote .env from .env.example (local Ollama defaults)."
  echo "On a RunPod GPU pod, run scripts/install_vllm.sh next to point GraphRAG at vLLM."
fi

echo "Prerequisites installed. Activate the environment with: source .venv/bin/activate"
