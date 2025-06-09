# 필요한 라이브러리 임포트
from dataclasses import dataclass
from typing import List

@dataclass
class Subject:
    """과목 정보를 담는 데이터 클래스"""
    name: str  # 과목명
    teachers: List[str]  # 담당 교사 목록
    required: bool  # 필수 과목 여부

@dataclass
class Teacher:
    """교사 정보를 담는 데이터 클래스"""
    name: str  # 교사명
    home_room: str = None  # 담당 교실

@dataclass
class Location:
    """위치 정보를 담는 데이터 클래스"""
    building: str  # 건물명
    floor: int  # 층수
    room_number: str  # 호수
    x_coord: float  # X 좌표
    y_coord: float  # Y 좌표

@dataclass
class TimeSlot:
    """시간 정보를 담는 데이터 클래스"""
    day: str  # 요일
    period: int  # 교시
    start_time: str  # 시작 시간
    end_time: str  # 종료 시간 