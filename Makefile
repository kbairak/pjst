django:
	uv run src/examples/django_example/manage.py runserver

flask:
	uv run flask --app src.examples.flask_example.app run --reload


ruff:
	uv tool run ruff check --fix
	uv tool run ruff format
