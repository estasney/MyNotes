from functools import lru_cache, wraps
from pathlib import Path
from typing import Callable, ParamSpec

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from mynotes.notes_exporter.db.models import Base

HERE = Path(__file__)
HERE_DIR = HERE.parent

P = ParamSpec("P")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="MYNOTES_")
    BASE_DIR: Path = Field(HERE_DIR.parent, description="Root directory of the project")
    PROJECT_DIR: Path = Field(HERE_DIR, description="Directory of mynotes")
    PAGES_DIR: Path = Field(
        HERE_DIR.parent / "docs", description="Directory of the docs folder"
    )
    NOTES_DIR: Path = Field(
        HERE_DIR.parent / "notes", description="Directory of the notes folder"
    )
    INDEX_DIR: Path = Field(HERE_DIR / "src", description="Directory of the src folder")

    IGNORED_PAGES_DIR: list[str] = Field(
        ["static"], description="List of directories to ignore in the pages folder"
    )
    IGNORED_PAGES_FILES: list[str] = Field(
        [".nojekyll"], description="List of files to ignore in the pages folder"
    )
    DB_PATH: Path = Field(
        HERE_DIR.parent / "mynotes.db", description="Path to the database file"
    )
    DB_URL: str = Field(
        f"sqlite:///{HERE_DIR.parent / 'mynotes.db'}", description="URL to the database"
    )
    DEPLOYMENT_DOMAIN: str = Field(
        "https://estasney.github.io/MyNotes", description="Domain to deploy the notes"
    )
    PUBLIC_PATH: str = Field(
        "/MyNotes/static/dist/", description="Public path to the static dist folder"
    )
    STATIC_SRC: Path = Field(
        HERE_DIR / "mynotes" / "src" / "dist",
        description="Path to the static source folder",
    )
    STATIC_DIST: Path = Field(
        HERE_DIR.parent / "docs" / "static" / "dist",
        description="Path to the static dist folder",
    )
    HASHED_DIRS: list[Path] = Field(
        [HERE_DIR / "docs" / "static" / "dist"],
        description="List of hashed directories",
    )


@lru_cache(maxsize=1)
def get_settings(**kwargs: dict | None) -> Settings:
    return Settings(**kwargs)


def inject_settings[T, ** P](func: Callable[P, T]) -> Callable[P, T]:
    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        settings = get_settings()
        return func(settings, *args, **kwargs)

    return wrapper


@inject_settings
def get_session(settings: Settings) -> Session:
    engine = create_engine(settings.DB_URL)

    # create all tables
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    return session