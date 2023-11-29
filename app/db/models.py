from enum import Enum, auto
from typing import Optional, List
from datetime import datetime

from sqlmodel import SQLModel, Field, Relationship

from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import declared_attr


class Scope(Enum):
    """Represents a scope to categorize events.

    Attributes:
        ENTERTAINMENT: The entertainment scope.
        ENLIGHTENMENT: The enlightenment scope.
        EDUCATION: The ignored scope at the moment.
    """

    ENTERTAINMENT = auto()
    ENLIGHTENMENT = auto()
    EDUCATION = auto()


class BaseModel(SQLModel):
    """A base model for database entities.

    Attributes:
        id (Optional[int]): The unique identifier for this object.
        created_at (datetime): The identity date and time for this object.
        updated_at (datetime): The computed date and time for this object.
    """

    id: int = Field(primary_key=True)
    created_at: datetime = Field(default_factory=datetime.now)

    @declared_attr  # type: ignore
    def __tablename__(cls) -> str:
        return cls.__name__


class UniqueNamedModel(BaseModel):
    """A base model for unique named entities.

    Attributes:
        name (str): The unique name of this object.
    """

    name: str = Field(max_length=128, unique=True, index=True)


class Place(UniqueNamedModel, table=True):
    """A class representing a place.

    Attributes:
        areas (List[Area]): The list of areas associated with this place.
        events (List[Event]): The list of events associated with this place.
        assignments (List[Assignment]): The list of assignments associated with this place.
        reservations (List[Reservation]): The list of reservations associated with this place.
    """

    areas: List["Area"] = Relationship(
        back_populates="place",
        sa_relationship_kwargs={"cascade": "all, delete"},
    )
    events: List["Event"] = Relationship(back_populates="place")
    assignments: List["Assignment"] = Relationship(back_populates="place")
    reservations: List["Reservation"] = Relationship(back_populates="place")


class EventType(UniqueNamedModel, table=True):
    """A class representing an event type.

    Attributes:
        events (List[Event]): The list of events associated with this event type.
    """

    events: List["Event"] = Relationship(back_populates="type")


class Event(BaseModel, table=True):
    """Represents an event registered on a specific date.

    Attributes:
        title (str): The title of the event.
        description (Optional[str]): The description of the event.
        start_at (datetime): The start date and time of the event.
        scope (Scope): The scope of the event.
        type_id (Optional[int]): The unique identifier of the associated event type.
        type (Optional[EventType]): The event type associated with this event.
        place_id (Optional[int]): The unique identifier of the associated place.
        place (Optional[Place]): The associated place of the event.
        areas (List[Area]): The list of areas associated with this event.
        assignments (List[Assignment]): The list of assignments associated with this event.
        reservations (List[Reservation]): The list of reservations associated with this event.
    """

    title: str = Field(max_length=256, index=True)
    description: Optional[str] = Field(default=None, max_length=1028)
    start_at: datetime
    scope: Scope

    type_id: Optional[int] = Field(default=None, foreign_key="EventType.id")
    type: Optional[EventType] = Relationship(back_populates="events")

    place_id: Optional[int] = Field(default=None, foreign_key="Place.id")
    place: Optional[Place] = Relationship(back_populates="events")

    areas: List["Area"] = Relationship(back_populates="event")
    assignments: List["Assignment"] = Relationship(back_populates="event")
    reservations: List["Reservation"] = Relationship(back_populates="event")


class AssignmentType(UniqueNamedModel, table=True):
    """A class representing an assignment type.

    Attributes:
        assignments (List[Assignment]): The list of assignments associated with this assignment type.
    """

    assignments: List["Assignment"] = Relationship(back_populates="type")


class Assignment(BaseModel, table=True):
    """A class representing an assignment to an event.

    Attributes:
        state (State): The state of this assignment.
        deadline (datetime): The deadline of this assignment.
        description (Optional[str]): The description of this assignment.
        event_id (Optional[int]): The unique identifier of the associated event.
        event (Event): The event associated with this assignment.
        type_id (Optional[int]): The unique identifier of the assignment type.
        type (AssignmentType): The assignment type object.
        place_id (Optional[int]): The unique identifier of the associated place.
        place (Place): The place associated with this assignment.
    """

    class State(Enum):
        """Enumeration representing the state of an assignment.

        Attributes:
            DRAFT: The assignment is in the draft state.
            ACTIVE: The assignment is active at the moment.
            COMPLETED: The assignment has been marked as completed.
        """

        DRAFT = auto()
        ACTIVE = auto()
        COMPLETED = auto()

    state: State = State.DRAFT
    deadline: datetime
    description: Optional[str] = Field(default=None, max_length=1028)

    type_id: Optional[int] = Field(default=None, foreign_key="AssignmentType.id")
    type: Optional[AssignmentType] = Relationship(back_populates="assignments")

    place_id: Optional[int] = Field(default=None, foreign_key="Place.id")
    place: Optional[Place] = Relationship(back_populates="assignments")

    event_id: Optional[int] = Field(default=None, foreign_key="Event.id")
    event: Optional[Event] = Relationship(back_populates="assignments")


class Area(BaseModel, table=True):
    """A class representing a part of a place.

    Attributes:
        place_id (Optional[int]): The unique identifier of the associated place.
        place (Optional[Place]): The place associated with this area.
        event_id (Optional[int]): The unique identifier of the associated event.
        event (Optional[Event]): The event associated with this area.
    """

    name: str = Field(max_length=128, index=True)

    place_id: Optional[int] = Field(default=None, foreign_key="Place.id")
    place: Optional[Place] = Relationship(back_populates="areas")

    event_id: Optional[int] = Field(default=None, foreign_key="Event.id")
    event: Optional[Event] = Relationship(back_populates="areas")

    __table_args__ = (UniqueConstraint("name", "place_id"),)


class Reservation(BaseModel, table=True):
    """A class representing a place reservation for an event.

    Attributes:
        start_at (datetime): The start time of the reservation.
        end_at (datetime): The end time of the reservation.
        comment (Optional[str]): An optional comment for the reservation.
        place_id (Optional[int]): The unique identifier of the associated place.
        place (Place): The place associated with this reservation.
        event_id (Optional[int]): The unique identifier of the associated event.
        event (Event): The event associated with this reservation.
    """

    start_at: datetime
    end_at: datetime
    comment: Optional[str] = Field(default=None, max_length=1028)

    place_id: Optional[int] = Field(default=None, foreign_key="Place.id")
    place: Place = Relationship(back_populates="reservations")

    event_id: Optional[int] = Field(default=None, foreign_key="Event.id")
    event: Event = Relationship(back_populates="reservations")
