# Pipeline shortcuts. GraphRAG reads config/settings.yaml and stores artifacts under data/.
# LLM_BACKEND=ollama|vllm selects which profile in settings.yaml is used.
# The variables are exported before the GraphRAG CLI runs because
# `graphrag --root config` only auto-loads config/.env.

ROOT := $(abspath .)
CONFIG := $(ROOT)/config

LLM_BACKEND ?= ollama
GRAPHRAG_API_KEY ?= ollama

ifneq ("$(wildcard $(ROOT)/.env)","")
include $(ROOT)/.env
endif

ifeq ($(LLM_BACKEND),ollama)
GRAPHRAG_COMPLETION_MODEL_ID ?= ollama
GRAPHRAG_EMBEDDING_MODEL_ID ?= ollama
else ifeq ($(LLM_BACKEND),vllm)
GRAPHRAG_COMPLETION_MODEL_ID ?= vllm
GRAPHRAG_EMBEDDING_MODEL_ID ?= vllm
else
$(error LLM_BACKEND must be ollama or vllm, got '$(LLM_BACKEND)')
endif

export LLM_BACKEND
export GRAPHRAG_API_KEY
export GRAPHRAG_COMPLETION_MODEL_ID
export GRAPHRAG_EMBEDDING_MODEL_ID

.DEFAULT_GOAL := help

.PHONY: help backend install install-vllm serve-vllm parse index query query-global visualize

help: ## Show available targets
	@echo "Usage: make <target>"
	@echo "Backend: make index LLM_BACKEND=ollama|vllm  (default: $(LLM_BACKEND))"
	@echo
	@awk 'BEGIN {FS = ":.*##"} \
	  /^##@/ {printf "\n%s\n", substr($$0, 5)} \
	  /^[a-zA-Z0-9_-]+:.*##/ {printf "  %-16s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

##@ Setup
backend: ## Print the active Ollama or vLLM profile
	@echo "LLM_BACKEND=$(LLM_BACKEND)"
	@echo "completion=$(GRAPHRAG_COMPLETION_MODEL_ID) embedding=$(GRAPHRAG_EMBEDDING_MODEL_ID)"

install: ## Install uv, GraphRAG, Surya OCR, and parquet libraries
	bash scripts/install_prerequisites.sh

install-vllm: ## Install vLLM into .venv-vllm and set LLM_BACKEND=vllm in .env
	bash scripts/install_vllm.sh

serve-vllm: ## Start vLLM chat (:8000) and embedding (:8001) servers
	bash scripts/serve_vllm.sh

##@ Pipeline
parse: ## Parse PDFs in data/raw_documents into data/input
	uv run python scripts/parse_pdfs.py --input data/raw_documents --output data/input

index: ## Build the knowledge graph
	@echo "Indexing with LLM_BACKEND=$(LLM_BACKEND)"
	uv run graphrag index --root $(CONFIG)

query: ## Local search. Usage: make query Q="your question"
	@test -n "$(Q)" || (echo 'Usage: make query Q="your question"' && exit 1)
	uv run graphrag query --root $(CONFIG) --method local "$(Q)"

query-global: ## Global search. Usage: make query-global Q="your question"
	@test -n "$(Q)" || (echo 'Usage: make query-global Q="your question"' && exit 1)
	uv run graphrag query --root $(CONFIG) --method global "$(Q)"

visualize: ## Print entities and relationships from data/output
	uv run python scripts/visualize_graph.py --output data/output
