#!/usr/bin/env bash
# Start an OpenAI-compatible vLLM chat server and a separate embedding server.
# Logs and pid files are written under data/logs.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

CHAT_MODEL="${VLLM_CHAT_MODEL:-google/medgemma-4b-it}"
EMBED_MODEL="${VLLM_EMBED_MODEL:-nomic-ai/nomic-embed-text-v1.5}"
CHAT_PORT="${VLLM_CHAT_PORT:-8000}"
EMBED_PORT="${VLLM_EMBED_PORT:-8001}"
CHAT_LEN="${VLLM_MAX_MODEL_LEN:-16384}"
EMBED_LEN="${VLLM_EMBED_MAX_MODEL_LEN:-2048}"
CHAT_MEM="${VLLM_CHAT_GPU_MEMORY_UTILIZATION:-0.72}"
EMBED_MEM="${VLLM_EMBED_GPU_MEMORY_UTILIZATION:-0.18}"
LOG_DIR="${ROOT}/data/logs"

if [[ -x "${ROOT}/.venv-vllm/bin/vllm" ]]; then
  VLLM="${ROOT}/.venv-vllm/bin/vllm"
elif command -v vllm >/dev/null 2>&1; then
  VLLM="$(command -v vllm)"
else
  echo "vllm is not installed. Run: bash scripts/install_vllm.sh" >&2
  exit 1
fi

if ! command -v nvidia-smi >/dev/null 2>&1; then
  echo "nvidia-smi was not found. Refusing to start vLLM without a GPU." >&2
  exit 1
fi

mkdir -p "${LOG_DIR}"

if [[ -n "${HF_TOKEN:-}" ]]; then
  export HUGGING_FACE_HUB_TOKEN="${HF_TOKEN}"
fi

start_server() {
  local name="$1"
  local port="$2"
  shift 2
  local pid_file="${LOG_DIR}/vllm-${name}.pid"
  local log_file="${LOG_DIR}/vllm-${name}.log"
  if [[ -f "${pid_file}" ]] && kill -0 "$(cat "${pid_file}")" 2>/dev/null; then
    echo "${name} already running (pid $(cat "${pid_file}"))."
    return 0
  fi
  echo "Starting ${name} on port ${port}. Log: ${log_file}"
  nohup "${VLLM}" serve "$@" >"${log_file}" 2>&1 &
  echo $! >"${pid_file}"
}

wait_for_port() {
  local port="$1"
  local name="$2"
  local attempt
  for attempt in $(seq 1 90); do
    if python3 -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:${port}/v1/models', timeout=2)" >/dev/null 2>&1; then
      echo "${name} is ready on http://127.0.0.1:${port}/v1"
      return 0
    fi
    sleep 2
  done
  echo "${name} did not become ready. See ${LOG_DIR}/vllm-${name}.log" >&2
  return 1
}

start_server embed "${EMBED_PORT}" \
  "${EMBED_MODEL}" \
  --host 127.0.0.1 \
  --port "${EMBED_PORT}" \
  --task embed \
  --max-model-len "${EMBED_LEN}" \
  --gpu-memory-utilization "${EMBED_MEM}" \
  --trust-remote-code

start_server chat "${CHAT_PORT}" \
  "${CHAT_MODEL}" \
  --host 127.0.0.1 \
  --port "${CHAT_PORT}" \
  --max-model-len "${CHAT_LEN}" \
  --gpu-memory-utilization "${CHAT_MEM}"

wait_for_port "${EMBED_PORT}" embed
wait_for_port "${CHAT_PORT}" chat

echo "GraphRAG should use config/.env:"
echo "  chat       ${CHAT_MODEL}  -> http://127.0.0.1:${CHAT_PORT}/v1"
echo "  embeddings ${EMBED_MODEL} -> http://127.0.0.1:${EMBED_PORT}/v1"
