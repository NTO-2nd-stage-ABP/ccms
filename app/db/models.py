from typing import Optional
from datetime import datetime

from sqlmodel import SQLModel, Field, Relationship


class Base(SQLModel):
    id: Optional[int] = Field(primary_key=True)


class Space(Base, table=True):
    name: str


class Event(Base, table=True):
    name: str
    date: datetime
    space_id: int = Field(default=None, foreign_key="space.id")
    space: Space = Relationship(back_populates="space")
