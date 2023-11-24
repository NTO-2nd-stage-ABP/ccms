from datetime import datetime
from enum import Enum
from typing import Optional, List

from sqlmodel import SQLModel, Field, Relationship


class Section(Enum):
    """
    Represents a section to categorize events.
    """

    ENTERTAINMENT = 1
    ENLIGHTENMENT = 2
    EDUCATION = 3


class BaseModel(SQLModel):
    """
    Represents the base for defining models.
    """

    id: Optional[int] = Field(default=None, primary_key=True)


class BaseNamedModel(BaseModel):
    name: str = Field(nullable=False, unique=True, max_length=128, index=True)


class EventType(BaseNamedModel, table=True):
    """
    Represents the type of an event.
    """

    events: List["Event"] = Relationship(back_populates="type")


class RoomType(BaseNamedModel, table=True):
    works: List["WorkRequest"] = Relationship(back_populates="room")
    events: List["Event"] = Relationship(back_populates="room")


class Event(BaseModel, table=True):
    """
    Represents an event registered on a specific date.
    """

    name: str = Field(max_length=256)
    start_at: datetime
    created_at: datetime = Field(nullable=False, default_factory=datetime.now)
    description: Optional[str] = Field(default=None, max_length=1028)

    type_id: Optional[int] = Field(default=None, foreign_key="eventtype.id")
    type: EventType = Relationship(back_populates="events")

    room_id: Optional[int] = Field(default=None, foreign_key="roomtype.id")
    room: RoomType = Relationship(back_populates="events")

    section: Section

    works: List["WorkRequest"] = Relationship(back_populates="event")


class WorkRequestType(BaseNamedModel, table=True):
    works: List["WorkRequest"] = Relationship(back_populates="type")


class WorkRequest(BaseModel, table=True):
    class Status(Enum):
        DRAFT = 1
        ACTIVE = 2
        COMPLETED = 3
    
    description: Optional[str] = Field(default=None, max_length=1028)

    event_id: Optional[int] = Field(default=None, foreign_key="event.id")
    event: Event = Relationship(back_populates="works")

    type_id: Optional[int] = Field(default=None, foreign_key="workrequesttype.id")
    type: WorkRequestType = Relationship(back_populates="works")

    room_id: Optional[int] = Field(default=None, foreign_key="roomtype.id")
    room: RoomType = Relationship(back_populates="works")

    deadline: datetime = Field(nullable=False)
    created_at: datetime = Field(nullable=False, default_factory=datetime.now)

    status: Status = Field(nullable=False)
