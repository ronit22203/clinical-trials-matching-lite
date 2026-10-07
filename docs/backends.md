# Backends

Two profiles are defined in `config/settings.yaml`. You pick one. You do not edit the YAML to switch.

| | Ollama | vLLM |
| --- | --- | --- |
| Use | Local development | RunPod / production |
| `LLM_BACKEND` | `ollama` | `vllm` |
| Chat model | `medgemma-graphrag:4b` | `google/medgemma-4b-it` |
| Chat URL | `http://localhost:11434/v1` | `http://127.0.0.1:8000/v1` |
| Embeddings | `nomic-embed-text` | `nomic-ai/nomic-embed-text-v1.5` |
| Embed URL | `http://localhost:11434/v1` | `http://127.0.0.1:8001/v1` |

`medgemma-graphrag:4b` is the Ollama tag `medgemma:4b` with a 16384-token context. Create it once:

```bash
ollama pull medgemma:4b
ollama pull nomic-embed-text
printf 'FROM medgemma:4b\nPARAMETER num_ctx 16384\n' > /tmp/medgemma-graphrag.Modelfile
ollama create medgemma-graphrag:4b -f /tmp/medgemma-graphrag.Modelfile
```

## How the switch works

`.env` holds:

```bash
LLM_BACKEND=ollama
GRAPHRAG_API_KEY=ollama
```

Make reads that file and exports two names GraphRAG substitutes into `settings.yaml`:

- `GRAPHRAG_COMPLETION_MODEL_ID` becomes `ollama` or `vllm`
- `GRAPHRAG_EMBEDDING_MODEL_ID` becomes the same value

Every index and query step in the YAML uses those names, so chat and embeddings move together.

GraphRAG only auto-loads a `.env` next to `config/settings.yaml`. Make exports the repo-root `.env` before it starts the CLI, which is why the variables still resolve.

## Change it

For the machine, edit `.env`:

```bash
LLM_BACKEND=vllm
```

For one command, without editing the file:

```bash
make backend
make index LLM_BACKEND=ollama
make query LLM_BACKEND=vllm Q="Which embolic sites does this case describe?"
```

`make backend` prints the profile that the next index or query will use.

`scripts/install_vllm.sh` sets `LLM_BACKEND=vllm` in `.env` on the RunPod pod. Set it back to `ollama` when you are on your laptop again.
