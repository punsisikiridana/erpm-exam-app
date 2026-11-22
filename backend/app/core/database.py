from sqlmodel import SQLModel, Session, create_engine

from app.core.config import settings

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args)


def init_db() -> None:
    from app.models import models  # noqa: F401 (ensures models are registered before create_all)

    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
