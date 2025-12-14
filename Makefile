APP_NAME=smart-resume-builder
PORT?=7860

.PHONY: install run test docker-build docker-run clean

install:
	uv venv .venv
	uv pip install -r requirements.txt

run:
	uv run app.py

test:
	uv run pytest

docker-build:
	docker build -t $(APP_NAME) .

docker-run:
	docker run -p $(PORT):7860 $(APP_NAME)

clean:
	rm -rf .venv __pycache__ .pytest_cache
