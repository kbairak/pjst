django:
	uv run src/examples/django_example/manage.py runserver

flask:
	uv run flask --app src.examples.flask_example.app run --reload

fastapi:
	uv run fastapi dev src/examples/fastapi_example/app.py

ruff:
	uv tool run ruff check --fix
	uv tool run ruff format
