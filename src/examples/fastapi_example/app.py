from fastapi import FastAPI

from pjst.fastapi import register

from .views import ArticleResourceHandler

app = FastAPI()


register(app, ArticleResourceHandler)
