# Default target
all: help

# Target to display help information
help:
	@grep -E '^[a-zA-Z_-]+:.*?# .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?# "}; {printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2}'

.PHONY: setup
setup: ## Check that uv is installed
	@uv --version || echo 'Please install uv: https://docs.astral.sh/uv/getting-started/installation/'
	uv sync --all-groups

.PHONY: run-mage
run-mage: ## Run mage
	MAGE_REPO_PATH=$$(pwd) uv run mage start lodgify

.PHONY: lint
lint: # Run linting check
	uv run ruff check --fix

.PHONY: format
format: # Run format
	uv run ruff format

.PHONY: check
check: lint format  # Run both lint, format

.PHONY: clear-cache
clear-cache:
	rm -rf lodgify/.file_versions .ruff_cache .mypy_cache **/__pycache__




