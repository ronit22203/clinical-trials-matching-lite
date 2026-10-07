# Pipeline

Three steps. Each one is a Make target.

## 1. Parse

Put PDFs in `data/raw_documents/`.

```bash
make parse
```

This runs Surya OCR v2 and writes a `.txt` file per PDF into `data/input/`. GraphRAG only reads `.txt`.

On a Mac, install the OCR stack once:

```bash
uv pip install surya-ocr python-dotenv pyarrow
brew install llama.cpp
```

## 2. Index

```bash
make index
```

GraphRAG reads `data/input/`, calls the active backend, and writes parquet files plus LanceDB under `data/output/`. Chunks are 600 tokens. Requests run one at a time so a laptop does not stall.

The first local index of a short paper still takes a while, because every chunk is an LLM call.

## 3. Query

```bash
make query Q="Which embolic sites does this case describe?"
make query-global Q="Summarize the embolic complications."
```

`make query` is local search (specific facts). `make query-global` is global search (a summary across the graph).

```bash
make visualize
```

Prints entities and relationships after indexing has written `entities.parquet` and `relationships.parquet`.

## Same commands from Python

```bash
uv run healthcare-platform-lite parse
uv run healthcare-platform-lite index
uv run healthcare-platform-lite query "Which embolic sites does this case describe?"
```

The Python entrypoint uses the same `LLM_BACKEND` value as Make.
