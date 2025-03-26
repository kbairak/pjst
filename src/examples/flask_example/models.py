import datetime
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class ArticleModel(Base):
    __tablename__ = "articles_app_articlemodel"

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


engine = create_engine(
    "sqlite:///:memory:"
    if os.environ.get("TESTING", False)
    else "sqlite:///src/examples/db.sqlite3"
)
