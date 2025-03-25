from pjst.django import register

from .views import ArticleResourceHandler

urlpatterns = [
    *register(ArticleResourceHandler),
]
