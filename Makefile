.PHONY: install dev test lint run clean

install:
	pip install -e .
	python -m spacy download en_core_web_sm

dev:
	pip install -e ".[dev]"
	python -m spacy download en_core_web_sm

test:
	pytest tests/ -v

lint:
	ruff check src/ tests/
	ruff format --check src/ tests/

format:
	ruff format src/ tests/

run:
	python -m pseudopipe sample_data/toymakers_memo.txt

clean:
	rm -rf build/ dist/ *.egg-info src/*.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
