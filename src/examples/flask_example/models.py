import datetime
import os

from sqlmodel import Field, SQLModel, create_engine


class ArticleModel(SQLModel, table=True):
    __tablename__ = "articles_app_article"

    id: int = Field(primary_key=True, default=None)
    title: str
    content: str
    created_at: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc)
    )
    updated_at: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc),
        sa_column_kwargs={
            "onupdate": lambda: datetime.datetime.now(datetime.timezone.utc)
        },
    )


engine = create_engine(
    "sqlite:///:memory:"
    if os.environ.get("TESTING", False)
    else "sqlite:///src/examples/db.sqlite3"
)
