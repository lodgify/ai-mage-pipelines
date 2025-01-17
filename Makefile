# Default target
all: help

# Target to display help information
help:
	@grep -E '^[a-zA-Z_-]+:.*?# .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?# "}; {printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2}'

.PHONY: setup
setup: ## Check that uv is installed
	@uv --version || echo 'Please install uv: https://docs.astral.sh/uv/getting-started/installation/'
	uv sync --all-groups

.PHONY: lint
lint: # Run linting check
	uv run ruff check --fix

.PHONY: format
format: # Run format
	uv run ruff format

.PHONY: typecheck
typecheck: # Run mypy check
	uv run mypy

.PHONY: check
check: lint format typecheck  # Run both lint, format, and typecheck




