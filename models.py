from dataclasses import dataclass
from typing import List

@dataclass
class Subject:
    name: str
    teachers: List[str]
    required: bool

@dataclass
class Teacher:
    name: str
    home_room: str = None

@dataclass
class Location:
    building: str
    floor: int
    room_number: str
    x_coord: float
    y_coord: float

@dataclass
class TimeSlot:
    day: str
    period: int
    start_time: str
    end_time: str 