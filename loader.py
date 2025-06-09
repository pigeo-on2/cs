# 필요한 라이브러리 임포트
import pandas as pd
from models import Subject, Teacher, Location, TimeSlot
from typing import List

class DataLoader:
    """데이터 로딩을 담당하는 클래스"""
    def __init__(self, data_dir='data'):
        """데이터 로더 초기화
        Args:
            data_dir (str): 데이터 파일이 저장된 디렉토리 경로
        """
        self.data_dir = data_dir
        self.subjects = self.load_subjects()
        self.teachers = self.load_teachers()
        self.locations = self.load_locations()
        self.time_slots = self.load_time_slots()
        self.teacher_assignments = self.load_teacher_assignments()

    def load_subjects(self) -> List[Subject]:
        """과목 정보 로드
        Returns:
            List[Subject]: 과목 객체 리스트
        """
        df = pd.read_csv(f'{self.data_dir}/subjects.csv')
        return [Subject(row['subject'], row['teachers'].split(','), row['required'] == 'true') for _, row in df.iterrows()]

    def load_teachers(self) -> List[Teacher]:
        """교사 정보 로드
        Returns:
            List[Teacher]: 교사 객체 리스트
        """
        # 모든 과목의 teacher를 합쳐서 유니크하게 만듦
        teachers = set()
        for subj in self.load_subjects():
            teachers.update(subj.teachers)
        return [Teacher(name) for name in teachers if name]

    def load_locations(self) -> List[Location]:
        """위치 정보 로드
        Returns:
            List[Location]: 위치 객체 리스트
        """
        df = pd.read_csv(f'{self.data_dir}/locations.csv')
        return [Location(row['building'], int(row['floor']), row['room_number'], float(row['x_coord']), float(row['y_coord'])) for _, row in df.iterrows()]

    def load_time_slots(self) -> List[TimeSlot]:
        """시간 정보 로드
        Returns:
            List[TimeSlot]: 시간 객체 리스트
        """
        df = pd.read_csv(f'{self.data_dir}/time_slots.csv')
        return [TimeSlot(row['day'], int(row['period']), row['start_time'], row['end_time']) for _, row in df.iterrows()]

    def load_teacher_assignments(self):
        """교사 배정 정보 로드
        Returns:
            list: 교사 배정 정보 딕셔너리 리스트
        """
        df = pd.read_csv(f'{self.data_dir}/teacher_assignments.csv')
        return df.to_dict('records') 