from typing import Final

from decouple import config

APP_NAME: Final[str] = config("APP_NAME")
DATABASE_URL: Final[str] = config("DATABASE_URL", default="sqlite:///db.sqlite3")
DATABASE_ECHO: Final[bool] = config("DATABASE_ECHO", default=False, cast=bool)
