# Healthcare Platform Lite

Local medical retrieval pipeline. Raw PDFs are parsed into text, Microsoft GraphRAG builds the knowledge graph, and queries run against a local Ollama model (`medgemma:4b`) with `nomic-embed-text`.

GraphRAG's project root is `config/`. Indexes, prompts, and source files stay under `data/`.

```
.
├── Makefile
├── README.md
├── pyproject.toml
├── uv.lock
├── config/
│   └── settings.yaml          # GraphRAG model, chunking, and storage settings
├── data/
│   ├── cache/                 # Pipeline execution cache
│   ├── input/                 # Cleaned text ingested by GraphRAG
│   ├── logs/
│   ├── output/                # Parquet artifacts and LanceDB
│   ├── prompts/
│   ├── raw_documents/         # Drop raw medical PDFs here before OCR
│   └── .env                   # GRAPHRAG_API_KEY=ollama
├── scripts/
│   ├── parse_pdfs.py          # PDF to text for data/input
│   └── visualize_graph.py     # Print entity and relationship tables
└── src/
    └── healthcare_platform_lite/
        ├── __init__.py
        ├── main.py            # parse | index | query | visualize
        └── query_engine.py    # GraphRAG CLI adapter
```

## Setup

Ollama needs the completion model, a context-extended tag, and the embedding model:

```bash
ollama pull medgemma:4b
ollama pull nomic-embed-text
```

`config/settings.yaml` calls `medgemma-graphrag:4b`, which is the same weights as `medgemma:4b` with a 16384-token context. Create that tag once:

```bash
printf 'FROM medgemma:4b\nPARAMETER num_ctx 16384\n' > /tmp/medgemma-graphrag.Modelfile
ollama create medgemma-graphrag:4b -f /tmp/medgemma-graphrag.Modelfile
```

`data/.env` contains `GRAPHRAG_API_KEY=ollama`. GraphRAG does not read that file on its own, because it looks for `.env` beside `config/settings.yaml`. The Makefile and `query_engine.py` export the key from `data/.env`.

GraphRAG is expected on `PATH` (this workspace uses the conda install). PDF parsing uses Docling when it is installed, and pypdf otherwise:

```bash
uv venv
uv pip install pypdf pyarrow
# optional layout-aware OCR
uv pip install docling
```

## Pipeline

```bash
# 1. PDFs in data/raw_documents -> .txt in data/input
make parse

# 2. Build the graph. One local request at a time; chunk size is 600.
make index

# 3. Ask a question
make query Q="Which embolic sites does this endocarditis case describe?"

# 4. List entities and relationships after indexing writes them
make visualize
```

The same steps are available through the package entrypoint:

```bash
uv run healthcare-platform-lite parse
uv run healthcare-platform-lite index
uv run healthcare-platform-lite query "Which embolic sites does this endocarditis case describe?"
uv run healthcare-platform-lite visualize
```

`make query` uses local search. `make query-global Q="..."` uses global search.

## Models

`config/settings.yaml` points both the chat and embedding clients at Ollama's OpenAI-compatible endpoint:

```yaml
completion_models:
  default_completion_model:
    model_provider: openai
    model: medgemma-graphrag:4b
    api_key: ${GRAPHRAG_API_KEY}
    api_base: http://localhost:11434/v1

embedding_models:
  default_embedding_model:
    model_provider: openai
    model: nomic-embed-text
    api_key: ${GRAPHRAG_API_KEY}
    api_base: http://localhost:11434/v1

concurrent_requests: 1
```

Storage paths in that file are relative to `config/` and land in `data/input`, `data/output`, `data/cache`, and `data/logs`.
