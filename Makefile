# Pipeline shortcuts. GraphRAG reads config/settings.yaml and stores artifacts under data/.
# Local Ollama defaults apply until config/.env (written by scripts/install_vllm.sh) overrides them.

ROOT := $(abspath .)
CONFIG := $(ROOT)/config

GRAPHRAG_API_KEY ?= ollama
GRAPHRAG_CHAT_MODEL ?= medgemma-graphrag:4b
GRAPHRAG_API_BASE ?= http://localhost:11434/v1
GRAPHRAG_EMBED_MODEL ?= nomic-embed-text
GRAPHRAG_EMBED_API_BASE ?= http://localhost:11434/v1

ifneq (,$(wildcard $(ROOT)/data/.env))
include $(ROOT)/data/.env
endif
ifneq (,$(wildcard $(CONFIG)/.env))
include $(CONFIG)/.env
endif

export GRAPHRAG_API_KEY
export GRAPHRAG_CHAT_MODEL
export GRAPHRAG_API_BASE
export GRAPHRAG_EMBED_MODEL
export GRAPHRAG_EMBED_API_BASE

.DEFAULT_GOAL := help

.PHONY: help install install-vllm serve-vllm parse index query query-global visualize

help: ## Show available targets
	@echo "Usage: make <target>"
	@echo
	@awk 'BEGIN {FS = ":.*##"} \
	  /^##@/ {printf "\n%s\n", substr($$0, 5)} \
	  /^[a-zA-Z0-9_-]+:.*##/ {printf "  %-16s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

##@ Setup
install: ## Install uv, GraphRAG, and PDF/parquet libraries
	bash scripts/install_prerequisites.sh

install-vllm: ## Install vLLM into .venv-vllm and write config/.env for RunPod
	bash scripts/install_vllm.sh

serve-vllm: ## Start vLLM chat (:8000) and embedding (:8001) servers
	bash scripts/serve_vllm.sh

##@ Pipeline
parse: ## Parse PDFs in data/raw_documents into data/input
	uv run python scripts/parse_pdfs.py --input data/raw_documents --output data/input

index: ## Build the knowledge graph
	uv run graphrag index --root $(CONFIG)

query: ## Local search. Usage: make query Q="your question"
	@test -n "$(Q)" || (echo 'Usage: make query Q="your question"' && exit 1)
	uv run graphrag query --root $(CONFIG) --method local "$(Q)"

query-global: ## Global search. Usage: make query-global Q="your question"
	@test -n "$(Q)" || (echo 'Usage: make query-global Q="your question"' && exit 1)
	uv run graphrag query --root $(CONFIG) --method global "$(Q)"

visualize: ## Print entities and relationships from data/output
	uv run python scripts/visualize_graph.py --output data/output
