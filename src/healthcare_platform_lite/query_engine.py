"""Adapters that run the local GraphRAG CLI against config/ and data/."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_ROOT = PROJECT_ROOT / "config"
ENV_FILE = PROJECT_ROOT / ".env"
BACKENDS = ("ollama", "vllm")
ENV_DEFAULTS = {
    "LLM_BACKEND": "ollama",
    "GRAPHRAG_API_KEY": "ollama",
}


def _load_repo_env() -> None:
    """Load the repo-root .env without overriding variables already in the shell."""
    try:
        from dotenv import load_dotenv
    except ImportError:
        if not ENV_FILE.is_file():
            return
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            key, value = stripped.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))
        return
    load_dotenv(dotenv_path=ENV_FILE, override=False)


def _graphrag_env() -> dict[str, str]:
    """Shell environment wins, then the repo-root .env, then local defaults.

    ``LLM_BACKEND`` selects the ``ollama`` or ``vllm`` profile in settings.yaml.
    GraphRAG only auto-loads a .env next to ``--root`` (``config/``), so this
    environment is passed in explicitly.
    """
    _load_repo_env()
    env = os.environ.copy()
    for key, value in ENV_DEFAULTS.items():
        env.setdefault(key, value)
    backend = env["LLM_BACKEND"]
    if backend not in BACKENDS:
        raise RuntimeError(f"LLM_BACKEND must be ollama or vllm, got {backend!r}")
    env.setdefault("GRAPHRAG_COMPLETION_MODEL_ID", backend)
    env.setdefault("GRAPHRAG_EMBEDDING_MODEL_ID", backend)
    return env


def _graphrag_command(*args: str) -> list[str]:
    executable = shutil.which("graphrag")
    if executable is None:
        raise RuntimeError("graphrag is not on PATH. Install it before querying or indexing.")
    return [executable, *args, "--root", str(CONFIG_ROOT)]


def run_index() -> subprocess.CompletedProcess[str]:
    """Build the knowledge graph using config/settings.yaml."""
    return subprocess.run(
        _graphrag_command("index"),
        cwd=PROJECT_ROOT,
        env=_graphrag_env(),
        check=True,
        text=True,
    )


def run_query(question: str, method: str = "local") -> str:
    """Run a GraphRAG query and return the CLI stdout."""
    result = subprocess.run(
        [*_graphrag_command("query", "--method", method), question],
        cwd=PROJECT_ROOT,
        env=_graphrag_env(),
        check=True,
        text=True,
        capture_output=True,
    )
    return result.stdout
