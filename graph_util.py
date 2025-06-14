# 필요한 라이브러리 임포트
import networkx as nx
import numpy as np
from typing import List, Dict, Tuple, Set
from datetime import datetime, timedelta
import logging

# 로거 설정
logger = logging.getLogger(__name__)

def build_graph(locations):
    """위치 정보를 기반으로 그래프 생성
    Args:
        locations (List[Location]): Location 객체 리스트
    Returns:
        nx.Graph: 거리와 계단 수를 가중치로 하는 완전 연결 그래프
    """
    G = nx.Graph()
    # 노드 추가
    for loc in locations:
        G.add_node(loc.room_number, 
                  building=loc.building,
                  floor=loc.floor,
                  x_coord=loc.x_coord,
                  y_coord=loc.y_coord)
    # 엣지 추가 (거리와 계단 수를 고려한 가중치)
    for i, a in enumerate(locations):
        for b in locations[i+1:]:
            dist = ((a.x_coord-b.x_coord)**2 + (a.y_coord-b.y_coord)**2)**0.5
            stairs = abs(a.floor-b.floor)
            weight = dist + stairs * 5  # 계단 가중치(예시)
            G.add_edge(a.room_number, b.room_number, weight=weight)
    return G

def shortest_path(G, start, end):
    """두 노드 간의 최단 경로 계산
    Args:
        G (nx.Graph): 그래프
        start: 시작 노드
        end: 도착 노드
    Returns:
        list: 최단 경로 노드 리스트
    """
    return nx.shortest_path(G, start, end, weight='weight')

class GraphUtil:
    """
    그래프 관련 유틸리티 함수들을 제공하는 클래스
    
    이 클래스는 위치 데이터를 그래프로 변환하고,
    최단 경로 탐색, 경로 최적화 등의 기능을 제공합니다.
    """
    
    def __init__(self):
        """GraphUtil 초기화"""
        self.graph = nx.Graph()  # 기본 그래프
        self.directed_graph = nx.DiGraph()  # 방향성 그래프
        self.location_map = {}  # 위치 ID를 노드로 매핑
        
    def create_graph(self, locations: List[Dict]) -> nx.Graph:
        """
        위치 데이터로부터 그래프 생성
        
        Args:
            locations (List[Dict]): 위치 정보 목록
            
        Returns:
            nx.Graph: 생성된 그래프
        """
        try:
            # 그래프 초기화
            self.graph.clear()
            self.location_map.clear()
            
            # 노드 추가
            for location in locations:
                node_id = location['id']
                self.graph.add_node(
                    node_id,
                    name=location['name'],
                    type=location['type'],
                    coordinates=location['coordinates']
                )
                self.location_map[node_id] = node_id
                
            # 엣지 추가
            for i, loc1 in enumerate(locations):
                for j, loc2 in enumerate(locations[i+1:], i+1):
                    # 위치 간 거리 계산
                    distance = self._calculate_distance(
                        loc1['coordinates'],
                        loc2['coordinates']
                    )
                    
                    # 엣지 추가 (거리를 가중치로 사용)
                    self.graph.add_edge(
                        loc1['id'],
                        loc2['id'],
                        weight=distance
                    )
                    
            logger.info(f"그래프 생성 완료: {len(locations)}개 노드")
            return self.graph
            
        except Exception as e:
            logger.error(f"그래프 생성 중 오류 발생: {str(e)}")
            return nx.Graph()
            
    def create_directed_graph(self,
                            locations: List[Dict],
                            time_windows: Dict[str, Tuple[datetime, datetime]] = None) -> nx.DiGraph:
        """
        시간 제약을 고려한 방향성 그래프 생성
        
        Args:
            locations (List[Dict]): 위치 정보 목록
            time_windows (Dict[str, Tuple[datetime, datetime]], optional): 시간대 정보
            
        Returns:
            nx.DiGraph: 생성된 방향성 그래프
        """
        try:
            # 그래프 초기화
            self.directed_graph.clear()
            self.location_map.clear()
            
            # 노드 추가
            for location in locations:
                node_id = location['id']
                self.directed_graph.add_node(
                    node_id,
                    name=location['name'],
                    type=location['type'],
                    coordinates=location['coordinates']
                )
                self.location_map[node_id] = node_id
                
            # 엣지 추가
            for i, loc1 in enumerate(locations):
                for j, loc2 in enumerate(locations):
                    if i != j:  # 자기 자신으로의 엣지는 제외
                        # 시간 제약 확인
                        if time_windows:
                            if not self._check_time_constraint(
                                loc1['id'],
                                loc2['id'],
                                time_windows
                            ):
                                continue
                                
                        # 위치 간 거리 계산
                        distance = self._calculate_distance(
                            loc1['coordinates'],
                            loc2['coordinates']
                        )
                        
                        # 이동 시간 계산 (거리 기반)
                        travel_time = self._calculate_travel_time(distance)
                        
                        # 엣지 추가 (이동 시간을 가중치로 사용)
                        self.directed_graph.add_edge(
                            loc1['id'],
                            loc2['id'],
                            weight=travel_time
                        )
                        
            logger.info(f"방향성 그래프 생성 완료: {len(locations)}개 노드")
            return self.directed_graph
            
        except Exception as e:
            logger.error(f"방향성 그래프 생성 중 오류 발생: {str(e)}")
            return nx.DiGraph()
            
    def find_shortest_path(self,
                          start_id: str,
                          end_id: str,
                          weight: str = 'weight') -> List[str]:
        """
        두 위치 간의 최단 경로 탐색
        
        Args:
            start_id (str): 시작 위치 ID
            end_id (str): 도착 위치 ID
            weight (str): 가중치 속성 이름
            
        Returns:
            List[str]: 최단 경로상의 위치 ID 목록
        """
        try:
            if not self.graph.has_node(start_id) or not self.graph.has_node(end_id):
                logger.error(f"존재하지 않는 노드: {start_id} 또는 {end_id}")
                return []
                
            # Dijkstra 알고리즘을 사용한 최단 경로 탐색
            path = nx.shortest_path(
                self.graph,
                source=start_id,
                target=end_id,
                weight=weight
            )
            
            logger.info(f"최단 경로 탐색 완료: {start_id} -> {end_id}")
            return path
            
        except nx.NetworkXNoPath:
            logger.warning(f"경로를 찾을 수 없음: {start_id} -> {end_id}")
            return []
        except Exception as e:
            logger.error(f"최단 경로 탐색 중 오류 발생: {str(e)}")
            return []
            
    def find_all_shortest_paths(self,
                               start_id: str,
                               end_id: str,
                               weight: str = 'weight') -> List[List[str]]:
        """
        두 위치 간의 모든 최단 경로 탐색
        
        Args:
            start_id (str): 시작 위치 ID
            end_id (str): 도착 위치 ID
            weight (str): 가중치 속성 이름
            
        Returns:
            List[List[str]]: 모든 최단 경로 목록
        """
        try:
            if not self.graph.has_node(start_id) or not self.graph.has_node(end_id):
                logger.error(f"존재하지 않는 노드: {start_id} 또는 {end_id}")
                return []
                
            # Yen's K-Shortest Paths 알고리즘을 사용한 모든 최단 경로 탐색
            paths = list(nx.shortest_simple_paths(
                self.graph,
                source=start_id,
                target=end_id,
                weight=weight
            ))
            
            logger.info(f"모든 최단 경로 탐색 완료: {start_id} -> {end_id}")
            return paths
            
        except nx.NetworkXNoPath:
            logger.warning(f"경로를 찾을 수 없음: {start_id} -> {end_id}")
            return []
        except Exception as e:
            logger.error(f"최단 경로 탐색 중 오류 발생: {str(e)}")
            return []
            
    def find_optimal_route(self,
                          locations: List[str],
                          start_id: str = None,
                          end_id: str = None) -> List[str]:
        """
        주어진 위치들을 방문하는 최적의 경로 탐색 (TSP)
        
        Args:
            locations (List[str]): 방문할 위치 ID 목록
            start_id (str, optional): 시작 위치 ID
            end_id (str, optional): 도착 위치 ID
            
        Returns:
            List[str]: 최적 경로상의 위치 ID 목록
        """
        try:
            # 위치 목록 검증
            if not locations:
                logger.error("위치 목록이 비어있습니다.")
                return []
                
            # 시작/도착 위치가 지정된 경우 검증
            if start_id and start_id not in locations:
                logger.error(f"시작 위치가 목록에 없음: {start_id}")
                return []
            if end_id and end_id not in locations:
                logger.error(f"도착 위치가 목록에 없음: {end_id}")
                return []
                
            # 위치 간 거리 행렬 계산
            n = len(locations)
            distance_matrix = np.zeros((n, n))
            
            for i, loc1 in enumerate(locations):
                for j, loc2 in enumerate(locations):
                    if i != j:
                        path = self.find_shortest_path(loc1, loc2)
                        if path:
                            # 경로의 총 거리 계산
                            total_distance = sum(
                                self.graph[path[k]][path[k+1]]['weight']
                                for k in range(len(path)-1)
                            )
                            distance_matrix[i, j] = total_distance
                        else:
                            distance_matrix[i, j] = float('inf')
                            
            # 시작/도착 위치가 지정된 경우 처리
            if start_id and end_id:
                start_idx = locations.index(start_id)
                end_idx = locations.index(end_id)
                
                # 시작/도착 위치를 제외한 나머지 위치들에 대해 TSP 해결
                remaining_locations = [loc for loc in locations if loc not in [start_id, end_id]]
                if remaining_locations:
                    remaining_indices = [locations.index(loc) for loc in remaining_locations]
                    sub_matrix = distance_matrix[remaining_indices][:, remaining_indices]
                    
                    # TSP 해결
                    route_indices = self._solve_tsp(sub_matrix)
                    
                    # 전체 경로 구성
                    route = [start_id]
                    route.extend([remaining_locations[i] for i in route_indices])
                    route.append(end_id)
                else:
                    route = [start_id, end_id]
            else:
                # 일반적인 TSP 해결
                route_indices = self._solve_tsp(distance_matrix)
                route = [locations[i] for i in route_indices]
                
            logger.info("최적 경로 탐색 완료")
            return route
            
        except Exception as e:
            logger.error(f"최적 경로 탐색 중 오류 발생: {str(e)}")
            return []
            
    def _calculate_distance(self,
                          coord1: Tuple[float, float],
                          coord2: Tuple[float, float]) -> float:
        """
        두 좌표 간의 거리 계산 (Haversine 공식)
        
        Args:
            coord1 (Tuple[float, float]): 첫 번째 좌표 (위도, 경도)
            coord2 (Tuple[float, float]): 두 번째 좌표 (위도, 경도)
            
        Returns:
            float: 두 좌표 간의 거리 (km)
        """
        # 지구 반경 (km)
        R = 6371.0
        
        # 라디안으로 변환
        lat1, lon1 = np.radians(coord1)
        lat2, lon2 = np.radians(coord2)
        
        # 위도와 경도의 차이
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        # Haversine 공식
        a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
        distance = R * c
        
        return distance
        
    def _calculate_travel_time(self, distance: float) -> float:
        """
        거리 기반 이동 시간 계산
        
        Args:
            distance (float): 이동 거리 (km)
            
        Returns:
            float: 예상 이동 시간 (분)
        """
        # 기본 이동 속도 (km/h)
        base_speed = 30
        
        # 이동 시간 계산 (분)
        travel_time = (distance / base_speed) * 60
        
        # 교통 상황에 따른 추가 시간 (임의의 값)
        traffic_factor = np.random.uniform(1.0, 1.5)
        travel_time *= traffic_factor
        
        return travel_time
        
    def _check_time_constraint(self,
                             from_id: str,
                             to_id: str,
                             time_windows: Dict[str, Tuple[datetime, datetime]]) -> bool:
        """
        시간 제약 조건 확인
        
        Args:
            from_id (str): 출발 위치 ID
            to_id (str): 도착 위치 ID
            time_windows (Dict[str, Tuple[datetime, datetime]]): 시간대 정보
            
        Returns:
            bool: 시간 제약 조건 만족 여부
        """
        if from_id not in time_windows or to_id not in time_windows:
            return True
            
        from_start, from_end = time_windows[from_id]
        to_start, to_end = time_windows[to_id]
        
        # 이동 시간 계산
        distance = self._calculate_distance(
            self.graph.nodes[from_id]['coordinates'],
            self.graph.nodes[to_id]['coordinates']
        )
        travel_time = self._calculate_travel_time(distance)
        
        # 도착 시간이 시간대 내에 있는지 확인
        arrival_time = from_start + timedelta(minutes=travel_time)
        return to_start <= arrival_time <= to_end
        
    def _solve_tsp(self, distance_matrix: np.ndarray) -> List[int]:
        """
        외판원 문제(TSP) 해결
        
        Args:
            distance_matrix (np.ndarray): 거리 행렬
            
        Returns:
            List[int]: 최적 경로의 인덱스 목록
        """
        n = len(distance_matrix)
        if n <= 2:
            return list(range(n))
            
        # 현재 최적 경로
        best_route = list(range(n))
        best_distance = float('inf')
        
        # 시작점을 기준으로 최적 경로 탐색
        for start_idx in range(n):
            current_route = [start_idx]
            unvisited = list(range(start_idx)) + list(range(start_idx+1, n))
            
            while unvisited:
                current = current_route[-1]
                next_idx = min(
                    unvisited,
                    key=lambda x: distance_matrix[current][x]
                )
                current_route.append(next_idx)
                unvisited.remove(next_idx)
                
            # 경로의 총 거리 계산
            total_distance = sum(
                distance_matrix[current_route[i]][current_route[i+1]]
                for i in range(len(current_route)-1)
            )
            
            if total_distance < best_distance:
                best_distance = total_distance
                best_route = current_route
                
        return best_route 