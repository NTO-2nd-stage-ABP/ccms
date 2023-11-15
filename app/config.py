from typing import Final

from decouple import config

DEBUG: Final[bool] = config("DEBUG", default=False, cast=bool)
APP_NAME: Final[str] = config("APP_NAME")
DATABASE_URL: Final[str] = config("DATABASE_URL", default="sqlite:///db.sqlite3")
