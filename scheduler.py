from graph_util import build_graph, shortest_path
import random
from loader import DataLoader
from models import Teacher, Location
import numpy as np
from typing import List, Dict, Tuple
from datetime import datetime, timedelta
import logging
from models import Vehicle, Delivery

# 로거 설정
logger = logging.getLogger(__name__)

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

class DeliveryScheduler:
    """
    배달 스케줄링을 담당하는 클래스
    
    이 클래스는 최적화된 경로를 바탕으로 실제 배달 스케줄을 생성하고 관리합니다.
    시간 제약, 차량 상태, 우선순위 등을 고려하여 효율적인 스케줄을 생성합니다.
    """
    
    def __init__(self):
        """DeliveryScheduler 초기화"""
        self.schedule_history = []  # 스케줄 이력 저장
        self.current_schedule = {}  # 현재 스케줄
        
    def create_schedule(self,
                       routes: Dict[str, List[Location]],
                       vehicles: List[Vehicle] = None,
                       deliveries: List[Delivery] = None) -> Dict[str, List[Dict]]:
        """
        배달 스케줄 생성
        
        Args:
            routes (Dict[str, List[Location]]): 최적화된 경로 딕셔너리
            vehicles (List[Vehicle], optional): 차량 정보 목록
            deliveries (List[Delivery], optional): 배달 정보 목록
            
        Returns:
            Dict[str, List[Dict]]: 차량 ID를 키로 하는 스케줄 딕셔너리
        """
        try:
            # 입력 데이터 검증
            if not self._validate_input(routes, vehicles, deliveries):
                return {}
                
            # 스케줄 초기화
            schedule = {}
            current_time = datetime.now()
            
            # 각 차량의 경로에 대해 스케줄 생성
            for vehicle_id, route in routes.items():
                vehicle_schedule = self._create_vehicle_schedule(
                    vehicle_id,
                    route,
                    current_time,
                    vehicles,
                    deliveries
                )
                
                if vehicle_schedule:
                    schedule[vehicle_id] = vehicle_schedule
                    
            # 스케줄 저장
            self._save_schedule(schedule)
            
            return schedule
            
        except Exception as e:
            logger.error(f"스케줄 생성 중 오류 발생: {str(e)}")
            return {}
            
    def _validate_input(self,
                       routes: Dict[str, List[Location]],
                       vehicles: List[Vehicle],
                       deliveries: List[Delivery]) -> bool:
        """
        입력 데이터 유효성 검사
        
        Args:
            routes (Dict[str, List[Location]]): 검사할 경로 딕셔너리
            vehicles (List[Vehicle]): 검사할 차량 목록
            deliveries (List[Delivery]): 검사할 배달 목록
            
        Returns:
            bool: 유효성 검사 통과 여부
        """
        if not routes:
            logger.error("경로 정보가 비어있습니다.")
            return False
            
        if vehicles is not None:
            for vehicle in vehicles:
                if not isinstance(vehicle, Vehicle):
                    logger.error(f"잘못된 차량 데이터 형식: {vehicle}")
                    return False
                    
        if deliveries is not None:
            for delivery in deliveries:
                if not isinstance(delivery, Delivery):
                    logger.error(f"잘못된 배달 데이터 형식: {delivery}")
                    return False
                    
        return True
        
    def _create_vehicle_schedule(self,
                               vehicle_id: str,
                               route: List[Location],
                               start_time: datetime,
                               vehicles: List[Vehicle],
                               deliveries: List[Delivery]) -> List[Dict]:
        """
        개별 차량의 스케줄 생성
        
        Args:
            vehicle_id (str): 차량 ID
            route (List[Location]): 차량의 경로
            start_time (datetime): 스케줄 시작 시간
            vehicles (List[Vehicle]): 차량 정보 목록
            deliveries (List[Delivery]): 배달 정보 목록
            
        Returns:
            List[Dict]: 차량의 스케줄 목록
        """
        schedule = []
        current_time = start_time
        
        # 차량 정보 찾기
        vehicle = next((v for v in vehicles if v.id == vehicle_id), None) if vehicles else None
        
        # 각 위치에 대한 스케줄 생성
        for i, location in enumerate(route):
            # 위치 도착 시간 계산
            if i > 0:
                prev_location = route[i-1]
                travel_time = self._calculate_travel_time(prev_location, location, vehicle)
                current_time += timedelta(minutes=travel_time)
                
            # 위치별 작업 시간 계산
            operation_time = self._calculate_operation_time(location, vehicle)
            
            # 스케줄 항목 생성
            schedule_item = {
                'location_id': location.id,
                'location_name': location.name,
                'arrival_time': current_time.isoformat(),
                'operation_time': operation_time,
                'departure_time': (current_time + timedelta(minutes=operation_time)).isoformat(),
                'type': location.type
            }
            
            # 배달 정보가 있는 경우 추가
            if deliveries:
                delivery = self._find_delivery_for_location(location, deliveries)
                if delivery:
                    schedule_item['delivery_id'] = delivery.id
                    schedule_item['priority'] = delivery.priority
                    
            schedule.append(schedule_item)
            
            # 다음 위치로 이동하기 전에 현재 시간 업데이트
            current_time += timedelta(minutes=operation_time)
            
        return schedule
        
    def _calculate_travel_time(self,
                             from_location: Location,
                             to_location: Location,
                             vehicle: Vehicle = None) -> int:
        """
        두 위치 간 이동 시간 계산
        
        Args:
            from_location (Location): 출발 위치
            to_location (Location): 도착 위치
            vehicle (Vehicle, optional): 차량 정보
            
        Returns:
            int: 예상 이동 시간 (분)
        """
        # 기본 이동 속도 (km/h)
        base_speed = 30
        
        # 차량이 있는 경우 차량 상태에 따른 속도 조정
        if vehicle:
            if vehicle.status == 'maintenance':
                base_speed *= 0.5  # 정비 중인 차량은 속도 50% 감소
            elif vehicle.fuel_level < 30:
                base_speed *= 0.7  # 연료 부족 시 속도 30% 감소
                
        # 위치 간 거리 계산 (Haversine 공식 사용)
        lat1, lon1 = from_location.coordinates
        lat2, lon2 = to_location.coordinates
        
        # 지구 반경 (km)
        R = 6371.0
        
        # 라디안으로 변환
        lat1_rad = np.radians(lat1)
        lon1_rad = np.radians(lon1)
        lat2_rad = np.radians(lat2)
        lon2_rad = np.radians(lon2)
        
        # 위도와 경도의 차이
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        # Haversine 공식
        a = np.sin(dlat/2)**2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon/2)**2
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
        distance = R * c
        
        # 이동 시간 계산 (분)
        travel_time = (distance / base_speed) * 60
        
        # 교통 상황에 따른 추가 시간 (임의의 값)
        traffic_factor = np.random.uniform(1.0, 1.5)
        travel_time *= traffic_factor
        
        return int(travel_time)
        
    def _calculate_operation_time(self,
                                location: Location,
                                vehicle: Vehicle = None) -> int:
        """
        위치에서의 작업 시간 계산
        
        Args:
            location (Location): 작업 위치
            vehicle (Vehicle, optional): 차량 정보
            
        Returns:
            int: 예상 작업 시간 (분)
        """
        # 기본 작업 시간 (분)
        base_time = 15
        
        # 위치 유형에 따른 작업 시간 조정
        if location.type == 'pickup':
            base_time *= 1.2  # 픽업은 20% 더 오래 걸림
        elif location.type == 'delivery':
            base_time *= 1.5  # 배달은 50% 더 오래 걸림
            
        # 차량이 있는 경우 차량 상태에 따른 작업 시간 조정
        if vehicle:
            if vehicle.status == 'maintenance':
                base_time *= 1.3  # 정비 중인 차량은 30% 더 오래 걸림
            elif vehicle.fuel_level < 30:
                base_time *= 1.2  # 연료 부족 시 20% 더 오래 걸림
                
        # 날씨, 시간대 등에 따른 추가 시간 (임의의 값)
        additional_factor = np.random.uniform(1.0, 1.3)
        base_time *= additional_factor
        
        return int(base_time)
        
    def _find_delivery_for_location(self,
                                  location: Location,
                                  deliveries: List[Delivery]) -> Delivery:
        """
        위치에 해당하는 배달 정보 찾기
        
        Args:
            location (Location): 검색할 위치
            deliveries (List[Delivery]): 배달 정보 목록
            
        Returns:
            Delivery: 해당 위치의 배달 정보
        """
        for delivery in deliveries:
            if (delivery.pickup_location.id == location.id or
                delivery.delivery_location.id == location.id):
                return delivery
        return None
        
    def _save_schedule(self, schedule: Dict[str, List[Dict]]):
        """
        스케줄 저장
        
        Args:
            schedule (Dict[str, List[Dict]]): 저장할 스케줄
        """
        schedule_data = {
            'timestamp': datetime.now().isoformat(),
            'schedule': schedule
        }
        
        self.schedule_history.append(schedule_data)
        self.current_schedule = schedule
        
        logger.info("스케줄이 저장되었습니다.")
        
    def get_current_schedule(self) -> Dict[str, List[Dict]]:
        """
        현재 스케줄 조회
        
        Returns:
            Dict[str, List[Dict]]: 현재 스케줄
        """
        return self.current_schedule
        
    def get_schedule_history(self) -> List[Dict]:
        """
        스케줄 이력 조회
        
        Returns:
            List[Dict]: 스케줄 이력
        """
        return self.schedule_history
        
    def clear_history(self):
        """스케줄 이력 초기화"""
        self.schedule_history.clear()
        logger.info("스케줄 이력이 초기화되었습니다.") 