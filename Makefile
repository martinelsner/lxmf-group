VENV = .venv

.PHONY: help venv install test build release clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*##' $(MAKEFILE_LIST) | awk -F ':.*## ' '{printf "  %-10s %s\n", $$1, $$2}'

venv: ## Create a virtual environment
	uv venv --allow-existing $(VENV)

install: venv ## Install the project in editable mode with dev deps
	uv pip install --python $(VENV)/bin/python --editable ".[dev]"

test: install ## Run the test suite
	$(VENV)/bin/pytest tests/

build: install ## Build sdist and wheel for PyPI
	uv build

release: part = patch
release: install test ## Bump version, commit, and tag (part=patch|minor|major)
	git add --all
	git diff --quiet --staged || git commit
	$(VENV)/bin/bump-my-version bump $(part)
	@version=$$($(VENV)/bin/bump-my-version show current_version) && \
	echo "Tagging v$$version — enter release notes (opens editor)..." && \
	git tag -a "v$$version" --edit -m "v$$version"
	git push --follow-tags

clean: ## Remove the venv and build artifacts
	rm --recursive --force $(VENV) *.egg-info dist/ build/ result
