from flask import Flask
from sqlmodel import create_engine

from pjst.flask import register

from .views import ArticleResource


def create_app():
    app = Flask(__name__)
    register(app, ArticleResource)
    return app
