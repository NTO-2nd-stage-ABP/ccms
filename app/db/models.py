from enum import Enum
from typing import Optional, List
from datetime import datetime

from sqlmodel import SQLModel, Field, Relationship


class BaseModel(SQLModel):
    """
    Represents the base for defining models.
    """

    id: Optional[int] = Field(default=None, primary_key=True)


class Section(Enum):
    """
    Represents a section to categorize events.
    """

    ENTERTAINMENT = 1
    ENLIGHTENMENT = 2
    EDUCATION = 3


class EventType(BaseModel, table=True):
    """
    Represents the type of an event.
    """

    name: str = Field(default=None, max_length=256, unique=True)

    events: List["Event"] = Relationship(back_populates="type")


class Event(BaseModel, table=True):
    """
    Represents an event registered on a specific date.
    """

    date: datetime
    description: Optional[str] = Field(default=None, max_length=1028)

    type_id: Optional[int] = Field(default=None, foreign_key="eventtype.id")
    type: EventType = Relationship(back_populates="events")

    section: Section
