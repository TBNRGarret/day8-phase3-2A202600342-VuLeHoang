.PHONY: install install-dev install-sqlite test lint typecheck run-scenarios grade-local clean

install:
	python -m pip install -e .

install-dev:
	python -m pip install -e '.[dev]'

install-sqlite:
	python -m pip install -e ".[sqlite]"

install-laptop:
	@echo "Run the setup script for your platform:"
	@echo "  Windows (PowerShell): .\\scripts\\setup_laptop.ps1 [-WithSqlite]"
	@echo "  Unix: ./scripts/setup_laptop.sh [sqlite]"
test:
	pytest

lint:
	ruff check src tests

typecheck:
	mypy src

run-scenarios:
	python -m langgraph_agent_lab.cli run-scenarios --config configs/lab.yaml --output outputs/metrics.json

grade-local:
	python -m langgraph_agent_lab.cli validate-metrics --metrics outputs/metrics.json

clean:
	rm -rf .pytest_cache .ruff_cache .mypy_cache htmlcov dist build *.egg-info outputs/*.json
