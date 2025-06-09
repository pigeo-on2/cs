import pandas as pd
from models import Subject, Teacher, Location, TimeSlot
from typing import List

class DataLoader:
    def __init__(self, data_dir='data'):
        self.data_dir = data_dir
        self.subjects = self.load_subjects()
        self.teachers = self.load_teachers()
        self.locations = self.load_locations()
        self.time_slots = self.load_time_slots()
        self.teacher_assignments = self.load_teacher_assignments()

    def load_subjects(self) -> List[Subject]:
        df = pd.read_csv(f'{self.data_dir}/subjects.csv')
        return [Subject(row['subject'], row['teachers'].split(','), row['required'] == 'true') for _, row in df.iterrows()]

    def load_teachers(self) -> List[Teacher]:
        # 모든 과목의 teacher를 합쳐서 유니크하게 만듦
        teachers = set()
        for subj in self.load_subjects():
            teachers.update(subj.teachers)
        return [Teacher(name) for name in teachers if name]

    def load_locations(self) -> List[Location]:
        df = pd.read_csv(f'{self.data_dir}/locations.csv')
        return [Location(row['building'], int(row['floor']), row['room_number'], float(row['x_coord']), float(row['y_coord'])) for _, row in df.iterrows()]

    def load_time_slots(self) -> List[TimeSlot]:
        df = pd.read_csv(f'{self.data_dir}/time_slots.csv')
        return [TimeSlot(row['day'], int(row['period']), row['start_time'], row['end_time']) for _, row in df.iterrows()]

    def load_teacher_assignments(self):
        df = pd.read_csv(f'{self.data_dir}/teacher_assignments.csv')
        return df.to_dict('records') 