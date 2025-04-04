django:
	uv run src/examples/django_example/manage.py runserver 8000

migrate:
	uv run src/examples/django_example/manage.py migrate

flask:
	uv run flask --app src.examples.flask_example.app run --reload --port 8000

fastapi:
	uv run fastapi dev src/examples/fastapi_example/app.py

ruff:
	uv run ruff check --fix
	uv run ruff format

test:
	env TESTING=1 uv run pytest

debugtest:
	env TESTING=1 uv run pytest -vvs
