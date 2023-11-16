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

    EDUCATION = 1
    ENLIGHTMENT = 2
    ENTERTAINMENT = 3


class Type(BaseModel, table=True):
    """
    Represents the type of an event.
    """

    name: str
    section: Section
    
    events: List["Event"] = Relationship(back_populates="type")


class Event(BaseModel, table=True):
    """
    Represents an event registered on a specific date.
    """

    date: datetime
    description: Optional[str] = None

    type_id: Optional[int] = Field(default=None, foreign_key="type.id")
    type: Type = Relationship(back_populates="events")
