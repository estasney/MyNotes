from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from  sqlalchemy.orm.session import Session
from mynotes.config import Config
from typing import NewType

Base = declarative_base()

def get_engine():
    config = Config()
    db_url = config.DB_PATH
    return create_engine(db_url)


def get_session() -> Session:
    engine = get_engine()
    session = sessionmaker(bind=engine)
    return session()
