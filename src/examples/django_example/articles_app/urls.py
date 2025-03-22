from pjst.django import register

from .views import ArticleResource

urlpatterns = [
    *register(ArticleResource),
]
