.PHONY: demo prod precompute eval test

demo:
	docker-compose --profile demo up --build

prod:
	docker-compose --profile prod up --build

precompute:
	python -m apollo.cli precompute --embedding bge

eval:
	python -m apollo.evaluate --embedding hash --llm dry-run data/generated_queries.jsonl

test:
	python -m pytest tests/ -v
