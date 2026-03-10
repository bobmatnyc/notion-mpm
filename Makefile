# ============================================================================
# Notion MPM - MCP Server for Notion
# ============================================================================
# Automates development, testing, and publishing workflows
#
# Quick start:
#   make help           - Show this help
#   make install        - Install package in dev mode (uv sync)
#   make test           - Run pytest (unit tests)
#   make check          - lint + type-check + test (full quality gate)
#   make build          - Build wheel and sdist
#
# Version & Release:
#   make version        - Show current version
#   make bump-patch     - Bump patch version (0.1.0 -> 0.1.1)
#   make bump-minor     - Bump minor version (0.1.0 -> 0.2.0)
#   make bump-major     - Bump major version (0.1.0 -> 1.0.0)
#   make publish        - Patch bump + check + build + PyPI + GitHub + tag + push
#   make publish-minor  - Minor bump + full release
#   make publish-major  - Major bump + full release
#   make publish-only   - Publish current version to PyPI (no bump)

# ============================================================================
# PHONY Target Declarations
# ============================================================================
.PHONY: help install install-dev sync
.PHONY: test test-cov test-live
.PHONY: lint format type-check check
.PHONY: clean build
.PHONY: version bump-patch bump-minor bump-major sync-versions
.PHONY: tag push push-tags
.PHONY: publish publish-minor publish-major publish-only pre-publish

# ============================================================================
# Shell Configuration (Strict Mode)
# ============================================================================
SHELL := bash
.SHELLFLAGS := -eu -o pipefail -c
MAKEFLAGS += --warn-undefined-variables
MAKEFLAGS += --no-builtin-rules

# ============================================================================
# Configuration Variables
# ============================================================================
BLUE   := \033[0;34m
GREEN  := \033[0;32m
YELLOW := \033[0;33m
RED    := \033[0;31m
NC     := \033[0m

BUILD_DIR  := build
DIST_DIR   := dist
PYTHON     := uv run python
PKG        := notion_mpm
PKG_SRC    := src/$(PKG)
VERSION_PY := $(PKG_SRC)/__version__.py
VERSION_F  := VERSION

all: help

# ============================================================================
# Help System
# ============================================================================

help: ## Show this help message
	@echo "Notion MPM - MCP Server for Notion"
	@echo "==================================="
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "$(BLUE)Development:$(NC)"
	@echo "  $(GREEN)make install$(NC)        - Install package in dev mode (uv sync)"
	@echo "  $(GREEN)make test$(NC)           - Run pytest (unit tests)"
	@echo "  $(GREEN)make test-cov$(NC)       - Run pytest with HTML coverage report"
	@echo "  $(GREEN)make test-live$(NC)      - Run live Notion API integration tests"
	@echo "  $(GREEN)make lint$(NC)           - Run ruff linter"
	@echo "  $(GREEN)make format$(NC)         - Format code with ruff"
	@echo "  $(GREEN)make type-check$(NC)     - Run mypy (strict)"
	@echo "  $(GREEN)make check$(NC)          - All quality gates: lint + type-check + test"
	@echo "  $(GREEN)make clean$(NC)          - Remove build artifacts and caches"
	@echo ""
	@echo "$(BLUE)Version Management:$(NC)"
	@echo "  $(GREEN)make version$(NC)        - Show current version"
	@echo "  $(GREEN)make bump-patch$(NC)     - Bump patch version (x.y.Z → x.y.Z+1)"
	@echo "  $(GREEN)make bump-minor$(NC)     - Bump minor version (x.Y.z → x.Y+1.0)"
	@echo "  $(GREEN)make bump-major$(NC)     - Bump major version (X.y.z → X+1.0.0)"
	@echo "  $(GREEN)make sync-versions$(NC)  - Sync VERSION → pyproject.toml + __version__.py"
	@echo ""
	@echo "$(BLUE)Publishing:$(NC)"
	@echo "  $(GREEN)make publish$(NC)        - Patch bump + check + PyPI + GitHub Release"
	@echo "  $(GREEN)make publish-minor$(NC)  - Minor bump + full release"
	@echo "  $(GREEN)make publish-major$(NC)  - Major bump + full release"
	@echo "  $(GREEN)make publish-only$(NC)   - Publish current version to PyPI (no bump)"
	@echo "  $(GREEN)make pre-publish$(NC)    - Run quality gate + token check (dry-run)"
	@echo ""
	@echo "$(BLUE)Git:$(NC)"
	@echo "  $(GREEN)make tag$(NC)            - Create annotated git tag for current version"
	@echo "  $(GREEN)make push$(NC)           - Push commits to origin"
	@echo "  $(GREEN)make push-tags$(NC)      - Push all tags to origin"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-18s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(BLUE)Version:$(NC) $$(cat $(VERSION_F) 2>/dev/null || echo 'unknown')"
	@echo "$(BLUE)Build:$(NC)   $$(cat BUILD_NUMBER 2>/dev/null || echo 'n/a')"

# ============================================================================
# Installation
# ============================================================================

install: ## Install package in dev mode via uv sync
	@echo "$(YELLOW)Installing notion-mpm in dev mode...$(NC)"
	@uv sync
	@echo "$(GREEN)Done. Run 'uv run notion-mpm --help' to verify.$(NC)"

install-dev: ## Install with all dev dependencies
	@echo "$(YELLOW)Installing notion-mpm with dev dependencies...$(NC)"
	@uv sync --all-extras
	@echo "$(GREEN)Done.$(NC)"

sync: ## Sync uv lockfile with pyproject.toml
	@uv sync

# ============================================================================
# Testing
# ============================================================================

test: ## Run pytest (unit tests, no live API calls)
	@echo "$(YELLOW)Running tests...$(NC)"
	@uv run pytest tests/ -v
	@echo "$(GREEN)Tests passed.$(NC)"

test-cov: ## Run pytest with HTML + terminal coverage report
	@echo "$(YELLOW)Running tests with coverage...$(NC)"
	@uv run pytest tests/ -v \
		--cov=$(PKG) \
		--cov-report=html \
		--cov-report=term-missing
	@echo "$(GREEN)Coverage report: htmlcov/index.html$(NC)"

test-live: ## Run live Notion API integration tests (requires NOTION_API_KEY in .env.local)
	@echo "$(YELLOW)Running live integration tests...$(NC)"
	@if [ ! -f .env.local ]; then \
		echo "$(RED)✗ .env.local not found — add NOTION_API_KEY$(NC)"; \
		exit 1; \
	fi
	@uv run pytest tests/ -v -m live
	@echo "$(GREEN)Live tests passed.$(NC)"

# ============================================================================
# Linting & Formatting
# ============================================================================

lint: ## Run ruff linter across src/, tests/, agents/
	@echo "$(YELLOW)Running ruff linter...$(NC)"
	@uv run ruff check src/ tests/ agents/
	@echo "$(GREEN)Linting passed.$(NC)"

format: ## Format code with ruff (auto-fix + format)
	@echo "$(YELLOW)Formatting code...$(NC)"
	@uv run ruff check src/ tests/ agents/ --fix || true
	@uv run ruff format src/ tests/ agents/
	@echo "$(GREEN)Formatting complete.$(NC)"

type-check: ## Run mypy (strict, uses pyproject.toml config)
	@echo "$(YELLOW)Running mypy...$(NC)"
	@uv run mypy src/
	@echo "$(GREEN)Type check passed.$(NC)"

check: lint type-check test ## Run all quality gates: lint + type-check + test
	@echo ""
	@echo "$(GREEN)All checks passed.$(NC)"

# ============================================================================
# Cleanup
# ============================================================================

clean: ## Remove build artifacts and caches
	@echo "$(YELLOW)Cleaning build artifacts...$(NC)"
	@rm -rf $(BUILD_DIR) $(DIST_DIR) *.egg-info $(PKG_SRC)/*.egg-info
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -name ".DS_Store" -delete 2>/dev/null || true
	@rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage
	@echo "$(GREEN)Clean complete.$(NC)"

# ============================================================================
# Build
# ============================================================================

build: clean ## Build wheel and sdist; bumps BUILD_NUMBER
	@echo "$(YELLOW)Building package...$(NC)"
	@# Increment build number
	@if [ -f BUILD_NUMBER ]; then \
		BUILD=$$(cat BUILD_NUMBER); \
		echo "$$((BUILD + 1))" > BUILD_NUMBER; \
	else \
		echo "1" > BUILD_NUMBER; \
	fi
	@echo "$(BLUE)Build #$$(cat BUILD_NUMBER)$(NC)"
	@uv build
	@echo "$(GREEN)Build complete:$(NC)"
	@ls -lh $(DIST_DIR)/

# ============================================================================
# Version Management
# ============================================================================

version: ## Show current version from VERSION file
	@cat $(VERSION_F)

sync-versions: ## Sync VERSION → pyproject.toml, __version__.py, src/PKG/VERSION
	@echo "$(YELLOW)Syncing version files...$(NC)"
	@V=$$(cat $(VERSION_F)); \
	echo "$$V" > $(PKG_SRC)/VERSION; \
	sed -i '' "s/^version = \"[^\"]*\"/version = \"$$V\"/" pyproject.toml 2>/dev/null || \
		sed -i  "s/^version = \"[^\"]*\"/version = \"$$V\"/" pyproject.toml; \
	sed -i '' "s/^__version__ = \"[^\"]*\"/__version__ = \"$$V\"/" $(VERSION_PY) 2>/dev/null || \
		sed -i  "s/^__version__ = \"[^\"]*\"/__version__ = \"$$V\"/" $(VERSION_PY); \
	echo "$(GREEN)All version files synced to $$V$(NC)"

_check-clean: ## (internal) Require clean working directory
	@if [ -n "$$(git status --porcelain 2>/dev/null)" ]; then \
		echo "$(RED)Error: working directory is dirty. Commit or stash changes first.$(NC)"; \
		git status --short; \
		exit 1; \
	fi

_check-main: ## (internal) Warn if not on main branch
	@BRANCH=$$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo 'unknown'); \
	if [ "$$BRANCH" != "main" ]; then \
		echo "$(YELLOW)Warning: not on main branch (currently: $$BRANCH)$(NC)"; \
		read -p "Continue anyway? [y/N] " confirm; \
		if [ "$$confirm" != "y" ] && [ "$$confirm" != "Y" ]; then \
			echo "$(RED)Aborted.$(NC)"; exit 1; \
		fi; \
	fi

bump-patch: _check-clean ## Bump patch version (x.y.Z → x.y.Z+1), sync all files
	@echo "$(YELLOW)Bumping patch version...$(NC)"
	@V=$$(cat $(VERSION_F)); \
	MAJ=$$(echo $$V | cut -d. -f1); \
	MIN=$$(echo $$V | cut -d. -f2); \
	PAT=$$(echo $$V | cut -d. -f3); \
	NEW="$$MAJ.$$MIN.$$((PAT + 1))"; \
	echo "$$NEW" > $(VERSION_F); \
	echo "$(GREEN)$$V → $$NEW$(NC)"
	@$(MAKE) sync-versions

bump-minor: _check-clean ## Bump minor version (x.Y.z → x.Y+1.0), sync all files
	@echo "$(YELLOW)Bumping minor version...$(NC)"
	@V=$$(cat $(VERSION_F)); \
	MAJ=$$(echo $$V | cut -d. -f1); \
	MIN=$$(echo $$V | cut -d. -f2); \
	NEW="$$MAJ.$$((MIN + 1)).0"; \
	echo "$$NEW" > $(VERSION_F); \
	echo "$(GREEN)$$V → $$NEW$(NC)"
	@$(MAKE) sync-versions

bump-major: _check-clean ## Bump major version (X.y.z → X+1.0.0), sync all files
	@echo "$(YELLOW)Bumping major version...$(NC)"
	@V=$$(cat $(VERSION_F)); \
	MAJ=$$(echo $$V | cut -d. -f1); \
	NEW="$$((MAJ + 1)).0.0"; \
	echo "$$NEW" > $(VERSION_F); \
	echo "$(GREEN)$$V → $$NEW$(NC)"
	@$(MAKE) sync-versions

# ============================================================================
# Git Operations
# ============================================================================

tag: ## Create annotated git tag for current version
	@V=$$(cat $(VERSION_F)); \
	echo "$(YELLOW)Creating annotated tag v$$V...$(NC)"; \
	git tag -a "v$$V" -m "Release v$$V"; \
	echo "$(GREEN)Tagged v$$V$(NC)"

push: ## Push commits to origin
	@echo "$(YELLOW)Pushing commits...$(NC)"
	@git push origin
	@echo "$(GREEN)Pushed.$(NC)"

push-tags: ## Push all tags to origin
	@echo "$(YELLOW)Pushing tags...$(NC)"
	@git push origin --tags
	@echo "$(GREEN)Tags pushed.$(NC)"

# ============================================================================
# PyPI Token Resolution
# Searches (in order):
#   1. .env.local                           (project-level override)
#   2. ../gworkspace-mcp/.env.local         (shared credentials)
# ============================================================================

define resolve_pypi_token
PYPI_TOKEN=""; \
if [ -f .env.local ]; then . .env.local; fi; \
if [ -z "$${PYPI_TOKEN:-}" ] && [ -f ../gworkspace-mcp/.env.local ]; then \
	. ../gworkspace-mcp/.env.local; \
fi; \
if [ -z "$${PYPI_TOKEN:-}" ]; then \
	echo "$(RED)✗ PYPI_TOKEN not found in .env.local or ../gworkspace-mcp/.env.local$(NC)"; \
	exit 1; \
fi
endef

# ============================================================================
# Pre-Publish Quality Gate
# ============================================================================

pre-publish: ## Run quality gates + token check before publishing
	@echo "$(BLUE)═══════════════════════════════════════════════════$(NC)"
	@echo "$(BLUE)  Pre-Publish Quality Gate$(NC)"
	@echo "$(BLUE)═══════════════════════════════════════════════════$(NC)"
	@$(MAKE) lint
	@$(MAKE) type-check
	@$(MAKE) test
	@echo ""
	@echo "$(YELLOW)Checking PyPI token...$(NC)"
	@PYPI_TOKEN=""; \
	if [ -f .env.local ]; then . .env.local; fi; \
	if [ -z "$${PYPI_TOKEN:-}" ] && [ -f ../gworkspace-mcp/.env.local ]; then \
		. ../gworkspace-mcp/.env.local; \
	fi; \
	if [ -z "$${PYPI_TOKEN:-}" ]; then \
		echo "$(RED)✗ PYPI_TOKEN not found — add to .env.local or ../gworkspace-mcp/.env.local$(NC)"; \
		exit 1; \
	else \
		echo "$(GREEN)✓ PYPI_TOKEN found$(NC)"; \
	fi
	@echo ""
	@echo "$(GREEN)═══════════════════════════════════════════════════$(NC)"
	@echo "$(GREEN)  Quality gate PASSED — ready to publish$(NC)"
	@echo "$(GREEN)═══════════════════════════════════════════════════$(NC)"

# ============================================================================
# Publishing Workflows
# All publish targets: pre-publish → bump → sync → commit → tag → push → build → PyPI → GitHub
# ============================================================================

publish: _check-clean _check-main pre-publish ## Bump patch + full release (PyPI + GitHub Release + annotated tag)
	@echo "$(BLUE)═══════════════════════════════════════════════════$(NC)"
	@echo "$(BLUE)  Publishing Patch Release$(NC)"
	@echo "$(BLUE)═══════════════════════════════════════════════════$(NC)"
	@V=$$(cat $(VERSION_F)); \
	MAJ=$$(echo $$V | cut -d. -f1); \
	MIN=$$(echo $$V | cut -d. -f2); \
	PAT=$$(echo $$V | cut -d. -f3); \
	NEW="$$MAJ.$$MIN.$$((PAT + 1))"; \
	echo "$(YELLOW)Version: $$V → $$NEW$(NC)"; \
	echo "$$NEW" > $(VERSION_F); \
	$(MAKE) sync-versions; \
	echo "$(GREEN)✓ Version files synced$(NC)"; \
	git add $(VERSION_F) $(PKG_SRC)/VERSION pyproject.toml $(VERSION_PY); \
	git commit -m "chore: bump version to $$NEW"; \
	echo "$(GREEN)✓ Committed$(NC)"; \
	git tag -a "v$$NEW" -m "Release v$$NEW"; \
	echo "$(GREEN)✓ Tagged v$$NEW$(NC)"; \
	git push origin && git push origin --tags; \
	echo "$(GREEN)✓ Pushed to origin$(NC)"; \
	rm -rf dist/; \
	$(MAKE) build; \
	echo "$(GREEN)✓ Built package$(NC)"; \
	PYPI_TOKEN=""; \
	if [ -f .env.local ]; then . .env.local; fi; \
	if [ -z "$${PYPI_TOKEN:-}" ] && [ -f ../gworkspace-mcp/.env.local ]; then . ../gworkspace-mcp/.env.local; fi; \
	UV_PUBLISH_TOKEN="$$PYPI_TOKEN" uv run twine upload dist/*; \
	echo "$(GREEN)✓ Published to PyPI$(NC)"; \
	if command -v gh >/dev/null 2>&1; then \
		gh release create "v$$NEW" \
			--title "v$$NEW" \
			--generate-notes \
			dist/* \
			&& echo "$(GREEN)✓ GitHub Release created$(NC)" \
			|| echo "$(YELLOW)⚠ GitHub Release failed (non-blocking)$(NC)"; \
	else \
		echo "$(YELLOW)⚠ gh CLI not found — skipping GitHub Release$(NC)"; \
	fi; \
	echo ""; \
	echo "$(GREEN)═══════════════════════════════════════════════════$(NC)"; \
	echo "$(GREEN)  ✓ notion-mpm $$NEW published$(NC)"; \
	echo "$(GREEN)  ✓ PyPI + GitHub Release + git tag v$$NEW$(NC)"; \
	echo "$(GREEN)═══════════════════════════════════════════════════$(NC)"

publish-minor: _check-clean _check-main pre-publish ## Bump minor + full release
	@echo "$(BLUE)═══════════════════════════════════════════════════$(NC)"
	@echo "$(BLUE)  Publishing Minor Release$(NC)"
	@echo "$(BLUE)═══════════════════════════════════════════════════$(NC)"
	@V=$$(cat $(VERSION_F)); \
	MAJ=$$(echo $$V | cut -d. -f1); \
	MIN=$$(echo $$V | cut -d. -f2); \
	NEW="$$MAJ.$$((MIN + 1)).0"; \
	echo "$(YELLOW)Version: $$V → $$NEW$(NC)"; \
	echo "$$NEW" > $(VERSION_F); \
	$(MAKE) sync-versions; \
	echo "$(GREEN)✓ Version files synced$(NC)"; \
	git add $(VERSION_F) $(PKG_SRC)/VERSION pyproject.toml $(VERSION_PY); \
	git commit -m "chore: bump version to $$NEW"; \
	echo "$(GREEN)✓ Committed$(NC)"; \
	git tag -a "v$$NEW" -m "Release v$$NEW"; \
	echo "$(GREEN)✓ Tagged v$$NEW$(NC)"; \
	git push origin && git push origin --tags; \
	echo "$(GREEN)✓ Pushed to origin$(NC)"; \
	rm -rf dist/; \
	$(MAKE) build; \
	echo "$(GREEN)✓ Built package$(NC)"; \
	PYPI_TOKEN=""; \
	if [ -f .env.local ]; then . .env.local; fi; \
	if [ -z "$${PYPI_TOKEN:-}" ] && [ -f ../gworkspace-mcp/.env.local ]; then . ../gworkspace-mcp/.env.local; fi; \
	UV_PUBLISH_TOKEN="$$PYPI_TOKEN" uv run twine upload dist/*; \
	echo "$(GREEN)✓ Published to PyPI$(NC)"; \
	if command -v gh >/dev/null 2>&1; then \
		gh release create "v$$NEW" \
			--title "v$$NEW" \
			--generate-notes \
			dist/* \
			&& echo "$(GREEN)✓ GitHub Release created$(NC)" \
			|| echo "$(YELLOW)⚠ GitHub Release failed (non-blocking)$(NC)"; \
	else \
		echo "$(YELLOW)⚠ gh CLI not found — skipping GitHub Release$(NC)"; \
	fi; \
	echo ""; \
	echo "$(GREEN)═══════════════════════════════════════════════════$(NC)"; \
	echo "$(GREEN)  ✓ notion-mpm $$NEW published$(NC)"; \
	echo "$(GREEN)  ✓ PyPI + GitHub Release + git tag v$$NEW$(NC)"; \
	echo "$(GREEN)═══════════════════════════════════════════════════$(NC)"

publish-major: _check-clean _check-main pre-publish ## Bump major + full release
	@echo "$(BLUE)═══════════════════════════════════════════════════$(NC)"
	@echo "$(BLUE)  Publishing Major Release$(NC)"
	@echo "$(BLUE)═══════════════════════════════════════════════════$(NC)"
	@V=$$(cat $(VERSION_F)); \
	MAJ=$$(echo $$V | cut -d. -f1); \
	NEW="$$((MAJ + 1)).0.0"; \
	echo "$(YELLOW)Version: $$V → $$NEW$(NC)"; \
	echo "$$NEW" > $(VERSION_F); \
	$(MAKE) sync-versions; \
	echo "$(GREEN)✓ Version files synced$(NC)"; \
	git add $(VERSION_F) $(PKG_SRC)/VERSION pyproject.toml $(VERSION_PY); \
	git commit -m "chore: bump version to $$NEW"; \
	echo "$(GREEN)✓ Committed$(NC)"; \
	git tag -a "v$$NEW" -m "Release v$$NEW"; \
	echo "$(GREEN)✓ Tagged v$$NEW$(NC)"; \
	git push origin && git push origin --tags; \
	echo "$(GREEN)✓ Pushed to origin$(NC)"; \
	rm -rf dist/; \
	$(MAKE) build; \
	echo "$(GREEN)✓ Built package$(NC)"; \
	PYPI_TOKEN=""; \
	if [ -f .env.local ]; then . .env.local; fi; \
	if [ -z "$${PYPI_TOKEN:-}" ] && [ -f ../gworkspace-mcp/.env.local ]; then . ../gworkspace-mcp/.env.local; fi; \
	UV_PUBLISH_TOKEN="$$PYPI_TOKEN" uv run twine upload dist/*; \
	echo "$(GREEN)✓ Published to PyPI$(NC)"; \
	if command -v gh >/dev/null 2>&1; then \
		gh release create "v$$NEW" \
			--title "v$$NEW" \
			--generate-notes \
			dist/* \
			&& echo "$(GREEN)✓ GitHub Release created$(NC)" \
			|| echo "$(YELLOW)⚠ GitHub Release failed (non-blocking)$(NC)"; \
	else \
		echo "$(YELLOW)⚠ gh CLI not found — skipping GitHub Release$(NC)"; \
	fi; \
	echo ""; \
	echo "$(GREEN)═══════════════════════════════════════════════════$(NC)"; \
	echo "$(GREEN)  ✓ notion-mpm $$NEW published$(NC)"; \
	echo "$(GREEN)  ✓ PyPI + GitHub Release + git tag v$$NEW$(NC)"; \
	echo "$(GREEN)═══════════════════════════════════════════════════$(NC)"

publish-only: ## Publish current version to PyPI (no bump, no tag, no push)
	@echo "$(BLUE)Publishing current version to PyPI...$(NC)"
	@rm -rf dist/
	@$(MAKE) build
	@PYPI_TOKEN=""; \
	if [ -f .env.local ]; then . .env.local; fi; \
	if [ -z "$${PYPI_TOKEN:-}" ] && [ -f ../gworkspace-mcp/.env.local ]; then . ../gworkspace-mcp/.env.local; fi; \
	if [ -z "$${PYPI_TOKEN:-}" ]; then \
		echo "$(RED)✗ PYPI_TOKEN not found$(NC)"; \
		exit 1; \
	fi; \
	UV_PUBLISH_TOKEN="$$PYPI_TOKEN" uv run twine upload dist/*
	@echo "$(GREEN)✓ Published to PyPI$(NC)"
