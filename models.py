# 필요한 라이브러리 임포트
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
import numpy as np
from datetime import datetime, timedelta
import logging

# 로거 설정
logger = logging.getLogger(__name__)

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
    """
    위치 정보를 나타내는 데이터 클래스
    
    Attributes:
        id (str): 위치 고유 식별자
        name (str): 위치 이름
        coordinates (Tuple[float, float]): 위도, 경도 좌표
        address (str): 상세 주소
        type (str): 위치 유형 (예: 'pickup', 'delivery', 'depot')
    """
    id: str
    name: str
    coordinates: Tuple[float, float]
    address: str
    type: str

@dataclass
class TimeSlot:
    """시간 정보를 담는 데이터 클래스"""
    day: str  # 요일
    period: int  # 교시
    start_time: str  # 시작 시간
    end_time: str  # 종료 시간 

@dataclass
class Vehicle:
    """
    차량 정보를 나타내는 데이터 클래스
    
    Attributes:
        id (str): 차량 고유 식별자
        capacity (float): 최대 적재 용량
        current_location (Location): 현재 위치
        status (str): 차량 상태 ('idle', 'busy', 'maintenance')
        fuel_level (float): 현재 연료 레벨 (0-100%)
        route (List[Location]): 현재 할당된 경로
    """
    id: str
    capacity: float
    current_location: Location
    status: str = 'idle'
    fuel_level: float = 100.0
    route: List[Location] = None

    def __post_init__(self):
        """초기화 후 처리"""
        if self.route is None:
            self.route = []
            
    def can_accept_delivery(self, delivery: 'Delivery') -> bool:
        """
        새로운 배달을 수용할 수 있는지 확인
        
        Args:
            delivery (Delivery): 확인할 배달 정보
            
        Returns:
            bool: 배달 수용 가능 여부
        """
        # 차량이 사용 가능한 상태인지 확인
        if self.status != 'idle':
            return False
            
        # 연료 레벨이 충분한지 확인
        if self.fuel_level < 20.0:  # 20% 미만이면 거부
            return False
            
        # 용량이 충분한지 확인
        current_load = sum(d.weight for d in self.route)
        if current_load + delivery.weight > self.capacity:
            return False
            
        return True
        
    def update_status(self, new_status: str):
        """
        차량 상태 업데이트
        
        Args:
            new_status (str): 새로운 상태
        """
        valid_statuses = ['idle', 'busy', 'maintenance']
        if new_status not in valid_statuses:
            logger.error(f"잘못된 차량 상태: {new_status}")
            return
            
        self.status = new_status
        logger.info(f"차량 {self.id}의 상태가 {new_status}로 변경되었습니다.")

@dataclass
class Delivery:
    """
    배달 정보를 나타내는 데이터 클래스
    
    Attributes:
        id (str): 배달 고유 식별자
        pickup_location (Location): 픽업 위치
        delivery_location (Location): 배달 위치
        weight (float): 배달 물품 무게
        volume (float): 배달 물품 부피
        priority (int): 우선순위 (높을수록 우선)
        time_window (Tuple[datetime, datetime]): 배달 시간대
        status (str): 배달 상태 ('pending', 'assigned', 'in_progress', 'completed')
    """
    id: str
    pickup_location: Location
    delivery_location: Location
    weight: float
    volume: float
    priority: int = 0
    time_window: Tuple[datetime, datetime] = None
    status: str = 'pending'

    def __post_init__(self):
        """초기화 후 처리"""
        if self.time_window is None:
            # 기본 시간대 설정 (현재 시간부터 2시간)
            now = datetime.now()
            self.time_window = (now, now + timedelta(hours=2))
            
    def is_within_time_window(self, current_time: datetime) -> bool:
        """
        주어진 시간이 배달 시간대 내에 있는지 확인
        
        Args:
            current_time (datetime): 확인할 시간
            
        Returns:
            bool: 시간대 내 여부
        """
        start_time, end_time = self.time_window
        return start_time <= current_time <= end_time
        
    def update_status(self, new_status: str):
        """
        배달 상태 업데이트
        
        Args:
            new_status (str): 새로운 상태
        """
        valid_statuses = ['pending', 'assigned', 'in_progress', 'completed']
        if new_status not in valid_statuses:
            logger.error(f"잘못된 배달 상태: {new_status}")
            return
            
        self.status = new_status
        logger.info(f"배달 {self.id}의 상태가 {new_status}로 변경되었습니다.")

class RouteOptimizer:
    """
    경로 최적화를 수행하는 클래스
    
    이 클래스는 주어진 배달 요청과 차량 정보를 바탕으로
    최적의 배달 경로를 계산합니다.
    """
    
    def __init__(self):
        """RouteOptimizer 초기화"""
        self.optimization_history = []  # 최적화 이력 저장
        
    def optimize(self, 
                deliveries: List[Delivery],
                vehicles: List[Vehicle],
                max_vehicles: int = 10,
                max_capacity: float = 1000.0,
                time_window: int = 3600) -> Dict[str, List[Location]]:
        """
        배달 경로 최적화 수행
        
        Args:
            deliveries (List[Delivery]): 최적화할 배달 목록
            vehicles (List[Vehicle]): 사용 가능한 차량 목록
            max_vehicles (int): 최대 사용 가능 차량 수
            max_capacity (float): 차량당 최대 적재 용량
            time_window (int): 최적화 시간대 (초)
            
        Returns:
            Dict[str, List[Location]]: 차량 ID를 키로 하는 최적화된 경로 딕셔너리
        """
        try:
            # 입력 데이터 검증
            if not self._validate_input(deliveries, vehicles):
                return {}
                
            # 우선순위에 따라 배달 정렬
            sorted_deliveries = sorted(deliveries, key=lambda x: x.priority, reverse=True)
            
            # 차량 할당 및 경로 생성
            routes = self._assign_vehicles(sorted_deliveries, vehicles, max_vehicles, max_capacity)
            
            # 경로 최적화
            optimized_routes = self._optimize_routes(routes, time_window)
            
            # 결과 저장
            self._save_optimization_result(optimized_routes)
            
            return optimized_routes
            
        except Exception as e:
            logger.error(f"경로 최적화 중 오류 발생: {str(e)}")
            return {}
            
    def _validate_input(self, deliveries: List[Delivery], vehicles: List[Vehicle]) -> bool:
        """
        입력 데이터 유효성 검사
        
        Args:
            deliveries (List[Delivery]): 검사할 배달 목록
            vehicles (List[Vehicle]): 검사할 차량 목록
            
        Returns:
            bool: 유효성 검사 통과 여부
        """
        if not deliveries:
            logger.error("배달 목록이 비어있습니다.")
            return False
            
        if not vehicles:
            logger.error("차량 목록이 비어있습니다.")
            return False
            
        # 배달 데이터 검사
        for delivery in deliveries:
            if not isinstance(delivery, Delivery):
                logger.error(f"잘못된 배달 데이터 형식: {delivery}")
                return False
                
        # 차량 데이터 검사
        for vehicle in vehicles:
            if not isinstance(vehicle, Vehicle):
                logger.error(f"잘못된 차량 데이터 형식: {vehicle}")
                return False
                
        return True
        
    def _assign_vehicles(self,
                        deliveries: List[Delivery],
                        vehicles: List[Vehicle],
                        max_vehicles: int,
                        max_capacity: float) -> Dict[str, List[Location]]:
        """
        차량 할당 및 초기 경로 생성
        
        Args:
            deliveries (List[Delivery]): 할당할 배달 목록
            vehicles (List[Vehicle]): 사용 가능한 차량 목록
            max_vehicles (int): 최대 사용 가능 차량 수
            max_capacity (float): 차량당 최대 적재 용량
            
        Returns:
            Dict[str, List[Location]]: 차량 ID를 키로 하는 초기 경로 딕셔너리
        """
        routes = {}
        assigned_vehicles = 0
        
        for delivery in deliveries:
            # 사용 가능한 차량 찾기
            assigned = False
            for vehicle in vehicles:
                if assigned_vehicles >= max_vehicles:
                    break
                    
                if vehicle.can_accept_delivery(delivery):
                    # 경로에 배달 추가
                    if vehicle.id not in routes:
                        routes[vehicle.id] = []
                        assigned_vehicles += 1
                        
                    routes[vehicle.id].extend([
                        delivery.pickup_location,
                        delivery.delivery_location
                    ])
                    
                    # 배달 상태 업데이트
                    delivery.update_status('assigned')
                    assigned = True
                    break
                    
            if not assigned:
                logger.warning(f"배달 {delivery.id}에 할당할 수 있는 차량이 없습니다.")
                
        return routes
        
    def _optimize_routes(self,
                        routes: Dict[str, List[Location]],
                        time_window: int) -> Dict[str, List[Location]]:
        """
        경로 최적화 수행
        
        Args:
            routes (Dict[str, List[Location]]): 최적화할 경로 딕셔너리
            time_window (int): 최적화 시간대 (초)
            
        Returns:
            Dict[str, List[Location]]: 최적화된 경로 딕셔너리
        """
        optimized_routes = {}
        
        for vehicle_id, route in routes.items():
            try:
                # 중복 위치 제거
                unique_locations = []
                for loc in route:
                    if loc not in unique_locations:
                        unique_locations.append(loc)
                        
                # 위치 간 거리 계산
                distances = self._calculate_distances(unique_locations)
                
                # 최적 경로 계산 (TSP 알고리즘 사용)
                optimized_route = self._solve_tsp(unique_locations, distances)
                
                optimized_routes[vehicle_id] = optimized_route
                
            except Exception as e:
                logger.error(f"차량 {vehicle_id}의 경로 최적화 중 오류 발생: {str(e)}")
                optimized_routes[vehicle_id] = route
                
        return optimized_routes
        
    def _calculate_distances(self, locations: List[Location]) -> np.ndarray:
        """
        위치 간 거리 계산
        
        Args:
            locations (List[Location]): 위치 목록
            
        Returns:
            np.ndarray: 거리 행렬
        """
        n = len(locations)
        distances = np.zeros((n, n))
        
        for i in range(n):
            for j in range(i + 1, n):
                # 위도, 경도 좌표를 사용하여 거리 계산
                lat1, lon1 = locations[i].coordinates
                lat2, lon2 = locations[j].coordinates
                
                # Haversine 공식을 사용한 거리 계산
                distance = self._haversine_distance(lat1, lon1, lat2, lon2)
                
                distances[i, j] = distance
                distances[j, i] = distance
                
        return distances
        
    def _haversine_distance(self,
                           lat1: float,
                           lon1: float,
                           lat2: float,
                           lon2: float) -> float:
        """
        Haversine 공식을 사용한 두 지점 간의 거리 계산
        
        Args:
            lat1 (float): 첫 번째 지점의 위도
            lon1 (float): 첫 번째 지점의 경도
            lat2 (float): 두 번째 지점의 위도
            lon2 (float): 두 번째 지점의 경도
            
        Returns:
            float: 두 지점 간의 거리 (km)
        """
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
        
        return distance
        
    def _solve_tsp(self,
                   locations: List[Location],
                   distances: np.ndarray) -> List[Location]:
        """
        외판원 문제(TSP) 해결
        
        Args:
            locations (List[Location]): 방문할 위치 목록
            distances (np.ndarray): 거리 행렬
            
        Returns:
            List[Location]: 최적 경로
        """
        n = len(locations)
        if n <= 2:
            return locations
            
        # 현재 최적 경로
        best_route = locations.copy()
        best_distance = float('inf')
        
        # 시작점을 기준으로 최적 경로 탐색
        for start_idx in range(n):
            current_route = [locations[start_idx]]
            unvisited = locations[:start_idx] + locations[start_idx+1:]
            
            while unvisited:
                current = current_route[-1]
                next_idx = np.argmin([
                    distances[locations.index(current)][locations.index(next)]
                    for next in unvisited
                ])
                current_route.append(unvisited.pop(next_idx))
                
            # 경로의 총 거리 계산
            total_distance = sum(
                distances[locations.index(current_route[i])][locations.index(current_route[i+1])]
                for i in range(len(current_route)-1)
            )
            
            if total_distance < best_distance:
                best_distance = total_distance
                best_route = current_route
                
        return best_route
        
    def _save_optimization_result(self, routes: Dict[str, List[Location]]):
        """
        최적화 결과 저장
        
        Args:
            routes (Dict[str, List[Location]]): 저장할 경로 딕셔너리
        """
        result = {
            'timestamp': datetime.now().isoformat(),
            'routes': {
                vehicle_id: [loc.id for loc in route]
                for vehicle_id, route in routes.items()
            }
        }
        
        self.optimization_history.append(result)
        logger.info("최적화 결과가 저장되었습니다.") 