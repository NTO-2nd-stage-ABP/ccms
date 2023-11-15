from typing import Final

from sqlmodel import create_engine
from sqlalchemy.future.engine import Engine

from app.config import DATABASE_URL, DATABASE_ECHO

ENGINE: Final[Engine] = create_engine(DATABASE_URL, echo=DATABASE_ECHO)
