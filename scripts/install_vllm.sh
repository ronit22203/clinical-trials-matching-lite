#!/usr/bin/env bash
# Install vLLM into .venv-vllm and set LLM_BACKEND=vllm in the repo-root .env.
# Model names and ports live in config/settings.yaml. Flip LLM_BACKEND back to
# ollama for local development.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

CHAT_MODEL="${VLLM_CHAT_MODEL:-google/medgemma-4b-it}"
EMBED_MODEL="${VLLM_EMBED_MODEL:-nomic-ai/nomic-embed-text-v1.5}"
CHAT_PORT="${VLLM_CHAT_PORT:-8000}"
EMBED_PORT="${VLLM_EMBED_PORT:-8001}"
VENV="${ROOT}/.venv-vllm"

install_uv() {
  if command -v uv >/dev/null 2>&1; then
    return 0
  fi
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="${HOME}/.local/bin:${PATH}"
}

if ! command -v nvidia-smi >/dev/null 2>&1; then
  echo "nvidia-smi was not found. Use a RunPod GPU pod; this script does not install drivers." >&2
  exit 1
fi

nvidia-smi

install_uv
uv venv "${VENV}" --python 3.11
uv pip install --python "${VENV}/bin/python" vllm huggingface_hub

ENV_FILE="${ROOT}/.env"
if [[ ! -f "${ENV_FILE}" ]]; then
  cp "${ROOT}/.env.example" "${ENV_FILE}"
fi
python3 - "${ENV_FILE}" <<'PY'
import sys
from pathlib import Path

path = sys.argv[1]
updates = {"LLM_BACKEND": "vllm"}
file_path = Path(path)
lines = file_path.read_text(encoding="utf-8").splitlines() if file_path.exists() else []
seen: set[str] = set()
rewritten: list[str] = []
for line in lines:
    stripped = line.strip()
    if stripped and not stripped.startswith("#") and "=" in line:
        key = line.split("=", 1)[0].strip()
        if key in updates:
            rewritten.append(f"{key}={updates[key]}")
            seen.add(key)
            continue
    rewritten.append(line)
for key, value in updates.items():
    if key not in seen:
        rewritten.append(f"{key}={value}")
file_path.write_text("\n".join(rewritten) + "\n", encoding="utf-8")
PY
echo "Set LLM_BACKEND=vllm in ${ENV_FILE}. Endpoints are the vllm profile in config/settings.yaml."

if [[ -n "${HF_TOKEN:-}" ]]; then
  export HUGGING_FACE_HUB_TOKEN="${HF_TOKEN}"
  echo "Downloading ${CHAT_MODEL} and ${EMBED_MODEL}..."
  "${VENV}/bin/huggingface-cli" download "${CHAT_MODEL}"
  "${VENV}/bin/huggingface-cli" download "${EMBED_MODEL}"
else
  echo "HF_TOKEN is unset. google/medgemma-4b-it is gated."
  echo "Accept the license at https://huggingface.co/google/medgemma-4b-it"
  echo "then export HF_TOKEN and re-run this script to prefetch the weights."
fi

echo "vLLM installed in ${VENV}."
echo "Start the servers with: bash scripts/serve_vllm.sh"
