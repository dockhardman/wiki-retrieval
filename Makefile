# Developing
logs:
	docker logs -f --tail 300 wiki-retrieval-service

install_all:
	poetry install --with dev --no-root

update_dependencies:
	poetry update
	poetry export --without-hashes -f requirements.txt --output requirements.txt
	poetry export --without-hashes -f requirements.txt --with dev --output requirements-dev.txt

format:
	poetry run black .
