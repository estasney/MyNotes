from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from mynotes.config import Config

Base = declarative_base()


def get_engine():
    config = Config()
    db_url = config.DB_PATH
    return create_engine(db_url)
