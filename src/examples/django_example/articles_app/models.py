from django.db import models


class Article(models.Model):
    id: int
    title = models.CharField(max_length=100)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Article(title={self.title!r}, ...)"
