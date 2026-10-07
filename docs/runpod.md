# RunPod

Use a GPU pod. The scripts do not install NVIDIA drivers.

```bash
bash scripts/install_prerequisites.sh
export HF_TOKEN=...    # google/medgemma-4b-it is a gated Hugging Face model
bash scripts/install_vllm.sh
bash scripts/serve_vllm.sh
make index LLM_BACKEND=vllm
```

`install_prerequisites.sh` installs uv, GraphRAG, and Surya OCR, and copies `.env.example` to `.env` if needed.

`install_vllm.sh` installs vLLM into `.venv-vllm` and sets `LLM_BACKEND=vllm`. Accept the MedGemma license on Hugging Face before the download will succeed.

`serve_vllm.sh` starts two OpenAI-compatible servers on that pod:

- chat on port 8000 (`google/medgemma-4b-it`, 16384 context)
- embeddings on port 8001 (`nomic-ai/nomic-embed-text-v1.5`)

Those ports match the `vllm` profile in `config/settings.yaml`. Logs go to `data/logs/vllm-chat.log` and `data/logs/vllm-embed.log`.

Then index and query as usual:

```bash
make index
make query Q="Which embolic sites does this case describe?"
```

With `LLM_BACKEND=vllm` already in `.env`, you can omit it on the command line.
