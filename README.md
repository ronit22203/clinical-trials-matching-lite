# Healthcare Platform Lite

Local medical retrieval. PDFs are parsed with Surya OCR v2, Microsoft GraphRAG builds the knowledge graph, and questions go to either Ollama on your machine or vLLM on RunPod.

GraphRAG's project root is `config/`. Text, prompts, and index files stay under `data/`.

```bash
# local
make index LLM_BACKEND=ollama

# production
make index LLM_BACKEND=vllm
```

Both profiles are in `config/settings.yaml`. The switch is `LLM_BACKEND` in `.env`. Details are in [docs/](docs/README.md).

| Doc | |
| --- | --- |
| [Pipeline](docs/pipeline.md) | parse, index, query |
| [Backends](docs/backends.md) | Ollama vs vLLM |
| [RunPod](docs/runpod.md) | install and serve vLLM |
