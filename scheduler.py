from graph_util import build_graph, shortest_path
import random
from loader import DataLoader
from models import Teacher, Location

class Scheduler:
    """시간표 생성 및 관리 클래스"""
    def __init__(self, loader: DataLoader):
        """스케줄러 초기화
        Args:
            loader (DataLoader): 데이터 로더 객체
        """
        self.loader = loader
        self.school_data = loader.load_school_data()
        self.locations = loader.load_locations()
        self.graph = build_graph(self.locations)
        self.rooms = [loc.room_number for loc in self.locations]
        self.teachers = loader.load_teachers()
        self.teacher_home_rooms = {t.name: t.home_room for t in self.teachers}

    def get_subjects(self):
        """전체 과목 목록 반환"""
        return list(set(row['과목'] for row in self.school_data))

    def get_classes(self):
        """전체 반 목록 반환"""
        all_classes = set()
        for row in self.school_data:
            for c in str(row['담당 반']).split(','):
                all_classes.add(c.strip())
        return sorted(all_classes)

    def calc_total_move(self, room_assignments, teacher_assignments):
        """전체 이동 거리 계산
        Args:
            room_assignments: 시간표와 동일한 구조, 각 칸에 교실 번호
            teacher_assignments: 시간표와 동일한 구조, 각 칸에 선생님 이름
        Returns:
            float: 전체 이동 거리
        """
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

    def generate(self, trials=1000):
        """시간표 생성
        Args:
            trials (int): 시도 횟수
        Returns:
            dict: 최적의 시간표
        """
        days = ['월요일', '화요일', '수요일', '목요일', '금요일']
        periods_per_day = {
            '월요일': 7,
            '화요일': 7,
            '수요일': 4,
            '목요일': 7,
            '금요일': 5
        }
        class_list = self.get_classes()
        best_timetables = None
        best_total_move = float('inf')
        for _ in range(trials):
            # 각 반의 시간표 초기화
            timetables = {class_num: {day: [None for _ in range(periods_per_day[day])] for day in days} for class_num in class_list}
            class_subject_slots = {}
            class_subject_count = {}
            
            # 각 반의 과목 정보 설정
            for class_num in class_list:
                class_rows = [row for row in self.school_data if class_num in str(row['담당 반']).split(',')]
                subject_slots = []
                subject_count = {}
                for row in class_rows:
                    count = int(row.get('주간시수', 1))
                    subject_count[row['과목']] = count
                    for _ in range(count):
                        subject_slots.append({
                            '과목': row['과목'],
                            '선생님': row['선생님'],
                            '교실': row['담당 교실']
                        })
                random.shuffle(subject_slots)
                class_subject_slots[class_num] = subject_slots
                class_subject_count[class_num] = subject_count.copy()
            
            # 시간표 생성
            idx_map = {c:0 for c in class_list}
            for day in days:
                for period in range(periods_per_day[day]):
                    used_teachers = set()
                    for class_num in class_list:
                        # 남은 시수가 있는 과목만 추출
                        available_slots = [slot for slot in class_subject_slots[class_num] if slot and class_subject_count[class_num].get(slot['과목'], 0) > 0 and slot['선생님'] not in used_teachers]
                        if available_slots:
                            slot = random.choice(available_slots)
                            class_subject_count[class_num][slot['과목']] -= 1
                            class_subject_slots[class_num].remove(slot)
                        else:
                            # 남은 시수가 모두 소진된 경우 None
                            slot = None
                        timetables[class_num][day][period] = slot
                        if slot and slot['선생님']:
                            used_teachers.add(slot['선생님'])
            
            # 이동 거리 계산 (반별 이동 거리의 합)
            total_move = 0
            for class_num in class_list:
                prev_room = None
                for day in days:
                    for period in range(periods_per_day[day]):
                        slot = timetables[class_num][day][period]
                        if slot and slot['교실']:
                            room = slot['교실']
                            if prev_room:
                                try:
                                    path = shortest_path(self.graph, prev_room, room)
                                    dist = sum(self.graph[u][v]['weight'] for u, v in zip(path, path[1:]))
                                    total_move += dist
                                except Exception:
                                    pass
                            prev_room = room
            
            # 최적의 시간표 업데이트
            if total_move < best_total_move:
                best_total_move = total_move
                best_timetables = timetables
        return best_timetables 