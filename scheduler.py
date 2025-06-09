from graph_util import build_graph, shortest_path
import random
from loader import DataLoader
from models import Teacher, Location

class Scheduler:
    def __init__(self, loader: DataLoader):
        self.loader = loader
        self.school_data = loader.load_school_data()
        self.locations = loader.load_locations()
        self.graph = build_graph(self.locations)
        self.rooms = [loc.room_number for loc in self.locations]
        self.teachers = loader.load_teachers()
        self.teacher_home_rooms = {t.name: t.home_room for t in self.teachers}

    def get_subjects(self):
        # 과목 리스트 반환
        return list(set(row['과목'] for row in self.school_data))

    def get_classes(self):
        # 전체 반 리스트 반환
        all_classes = set()
        for row in self.school_data:
            for c in str(row['담당 반']).split(','):
                all_classes.add(c.strip())
        return sorted(all_classes)

    def calc_total_move(self, room_assignments, teacher_assignments):
        # room_assignments: timetable와 동일한 구조, 각 칸에 교실 번호
        # teacher_assignments: timetable와 동일한 구조, 각 칸에 선생님 이름
        total = 0
        for day in range(len(room_assignments[0])):
            prev_room = None
            for period in range(len(room_assignments)):
                room = room_assignments[period][day]
                teacher = teacher_assignments[period][day]['teacher']
                
                # 선생님의 홈교실이 있는 경우, 해당 교실을 시작점으로 사용
                if prev_room is None and teacher in self.teacher_home_rooms:
                    prev_room = self.teacher_home_rooms[teacher]
                
                if prev_room:
                    path = shortest_path(self.graph, prev_room, room)
                    dist = sum(self.graph[u][v]['weight'] for u, v in zip(path, path[1:]))
                    total += dist
                prev_room = room
        return total

    def generate(self, trials=100):
        # 요일별 교시 수 반영
        days = ['월요일', '화요일', '수요일', '목요일', '금요일']
        periods_per_day = {
            '월요일': 7,
            '화요일': 7,
            '수요일': 4,
            '목요일': 7,
            '금요일': 5
        }
        class_list = self.get_classes()
        timetables = {}
        for class_num in class_list:
            timetable = {day: [None for _ in range(periods_per_day[day])] for day in days}
            # school_data에서 해당 반의 과목/교사/교실/주간시수만 추출
            class_rows = [row for row in self.school_data if class_num in str(row['담당 반']).split(',')]
            # 각 과목별로 주간시수만큼 배정할 셀 목록 생성
            subject_slots = []
            for row in class_rows:
                count = int(row.get('주간시수', 1))
                for _ in range(count):
                    subject_slots.append({
                        '과목': row['과목'],
                        '선생님': row['선생님'],
                        '교실': row['담당 교실']
                    })
            # 전체 셀 개수
            total_slots = sum(periods_per_day[day] for day in days)
            # 남는 시간은 None으로 채움
            while len(subject_slots) < total_slots:
                subject_slots.append(None)
            # 셔플하여 랜덤 배치
            random.shuffle(subject_slots)
            idx = 0
            for day in days:
                for j in range(periods_per_day[day]):
                    timetable[day][j] = subject_slots[idx]
                    idx += 1
            timetables[class_num] = timetable
        return timetables 