.PHONY: install index run test docker-up docker-down clean lint

install:
	pip install -r requirements.txt

index:
	python -m scripts.build_index

run:
	streamlit run app/streamlit_app.py

test:
	pytest tests/ -v

docker-up:
	docker compose up --build

docker-down:
	docker compose down

clean:
	rm -rf data/chroma .pytest_cache __pycache__ src/__pycache__ tests/__pycache__

lint:
	python -m py_compile src/*.py app/*.py scripts/*.py tests/*.py
