"""Adapters that run the local GraphRAG CLI against config/ and data/."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_ROOT = PROJECT_ROOT / "config"
ENV_FILES = (PROJECT_ROOT / "data" / ".env", CONFIG_ROOT / ".env")
ENV_DEFAULTS = {
    "GRAPHRAG_API_KEY": "ollama",
    "GRAPHRAG_CHAT_MODEL": "medgemma-graphrag:4b",
    "GRAPHRAG_API_BASE": "http://localhost:11434/v1",
    "GRAPHRAG_EMBED_MODEL": "nomic-embed-text",
    "GRAPHRAG_EMBED_API_BASE": "http://localhost:11434/v1",
}


def _parse_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def _graphrag_env() -> dict[str, str]:
    """Shell environment wins, then config/.env, then data/.env, then local defaults."""
    env = os.environ.copy()
    merged: dict[str, str] = {}
    for path in ENV_FILES:
        if path.is_file():
            merged.update(_parse_env_file(path))
    merged = {**ENV_DEFAULTS, **merged}
    for key, value in merged.items():
        env.setdefault(key, value)
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
