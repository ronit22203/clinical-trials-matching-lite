# Docs

Short notes for running this repo. Start with the page that matches what you are doing.

| Page | What it covers |
| --- | --- |
| [Pipeline](pipeline.md) | Parse a PDF, build the graph, ask a question |
| [Backends](backends.md) | Switch between Ollama on your machine and vLLM on RunPod |
| [RunPod](runpod.md) | Install and start vLLM on a GPU pod |

Settings live in `config/settings.yaml`. Source files, prompts, and index output live in `data/`. The switch itself is the `LLM_BACKEND` line in the repo-root `.env`.
