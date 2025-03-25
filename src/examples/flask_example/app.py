from flask import Flask

from pjst.flask import register

from .views import ArticleResourceHandler


def create_app():
    app = Flask(__name__)
    register(app, ArticleResourceHandler)
    return app
