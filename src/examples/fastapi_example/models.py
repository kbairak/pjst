import datetime
import os

from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class ArticleModel(Base):
    __tablename__ = "articles_app_article"

    id: Mapped[int | None] = mapped_column(primary_key=True, default=None)
    title: Mapped[str] = mapped_column()
    content: Mapped[str] = mapped_column()
    created_at: Mapped[datetime.datetime] = mapped_column(
        default=lambda: datetime.datetime.now(datetime.timezone.utc)
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        onupdate=lambda: datetime.datetime.now(datetime.timezone.utc),
    )


if os.environ.get("TESTING"):
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
else:
    engine = create_engine("sqlite:///src/examples/db.sqlite3")
