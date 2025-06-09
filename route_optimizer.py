from typing import List, Dict, Union
import pandas as pd
import networkx as nx
import math
from models import Location

class RouteOptimizer:
    """경로 최적화를 담당하는 클래스"""
    def __init__(self, loader):
        """경로 최적화기 초기화
        Args:
            loader: 데이터 로더 객체
        """
        self.locations = loader.load_locations()
        self.graph = self.create_graph(self.locations)

    def create_graph(self, locations: Union[pd.DataFrame, List[Dict]]) -> nx.Graph:
        """위치 정보를 기반으로 그래프 생성
        Args:
            locations: 위치 정보가 담긴 DataFrame 또는 리스트
        Returns:
            nx.Graph: 생성된 그래프
        """
        G = nx.Graph()
        
        # DataFrame이 아닌 경우 DataFrame으로 변환
        if not isinstance(locations, pd.DataFrame):
            locations = pd.DataFrame(locations)
        
        # elevator 컬럼이 없는 경우 추가 (기본값 0)
        if 'elevator' not in locations.columns:
            locations['elevator'] = 0
        
        # 노드 추가
        for _, row in locations.iterrows():
            G.add_node(row['room_number'], 
                      pos=(row['x_coord'], row['y_coord']),
                      building=row['building'],
                      floor=row['floor'],
                      elevator=row['elevator'])
        
        # 엣지 추가 (같은 건물, 같은 층 내 연결)
        for i, row1 in locations.iterrows():
            for j, row2 in locations.iterrows():
                if i < j and row1['building'] == row2['building'] and row1['floor'] == row2['floor']:
                    # 거리 계산
                    dist = ((row1['x_coord'] - row2['x_coord'])**2 + 
                           (row1['y_coord'] - row2['y_coord'])**2)**0.5
                    G.add_edge(row1['room_number'], row2['room_number'], 
                             weight=dist)
        
        # 엘리베이터가 있는 노드들 간의 연결 추가
        elevator_nodes = [node for node, data in G.nodes(data=True) if data.get('elevator', 0) == 1]
        for i, node1 in enumerate(elevator_nodes):
            for node2 in elevator_nodes[i+1:]:
                if G.nodes[node1]['building'] == G.nodes[node2]['building']:
                    # 층 차이에 따른 가중치 계산 (엘리베이터 사용)
                    floor_diff = abs(G.nodes[node1]['floor'] - G.nodes[node2]['floor'])
                    weight = floor_diff * 10  # 엘리베이터 사용 시 층당 10의 가중치
                    G.add_edge(node1, node2, weight=weight)
        
        # 건물별 1층 대표 노드 찾기
        building_representatives = {}
        for node, data in G.nodes(data=True):
            if data['floor'] == 1:
                building_representatives[data['building']] = node
        # 건물 내 모든 노드 ↔ 1층 대표 노드 연결 (층 차이만큼 가중치)
        for node, data in G.nodes(data=True):
            rep_node = building_representatives.get(data['building'])
            if rep_node and node != rep_node:
                floor_diff = abs(data['floor'] - G.nodes[rep_node]['floor'])
                G.add_edge(node, rep_node, weight=floor_diff * 10)
        # 건물 간 대표 노드끼리 연결 (임의의 거리 100)
        buildings = list(building_representatives.keys())
        for i in range(len(buildings)):
            for j in range(i+1, len(buildings)):
                node1 = building_representatives[buildings[i]]
                node2 = building_representatives[buildings[j]]
                G.add_edge(node1, node2, weight=100)
        
        return G
    
    def shortest_path(self, start: str, end: str) -> List[str]:
        """두 위치 간의 최단 경로 계산
        Args:
            start (str): 시작 위치
            end (str): 도착 위치
        Returns:
            List[str]: 상세 경로 정보 리스트
        """
        try:
            # 시작점과 끝점이 그래프에 존재하는지 확인
            if start not in self.graph or end not in self.graph:
                raise ValueError(f"시작점({start}) 또는 끝점({end})이 그래프에 존재하지 않습니다.")
            
            # 최단 경로 계산
            path = nx.shortest_path(self.graph, start, end, weight='weight')
            
            # 경로 상세 정보 생성
            detailed_path = []
            for i in range(len(path)-1):
                current = path[i]
                next_node = path[i+1]
                
                current_data = self.graph.nodes[current]
                next_data = self.graph.nodes[next_node]
                
                # 건물이 다른 경우
                if current_data['building'] != next_data['building']:
                    detailed_path.append(f"{current} → {next_node} (건물 이동)")
                # 층이 다른 경우
                elif current_data['floor'] != next_data['floor']:
                    if '엘리베이터' in current and '엘리베이터' in next_node:
                        detailed_path.append(f"{current} → {next_node} (엘리베이터 사용)")
                    else:
                        detailed_path.append(f"{current} → {next_node} (계단 사용)")
                # 같은 건물, 같은 층
                else:
                    detailed_path.append(f"{current} → {next_node}")
            
            return detailed_path
        except nx.NetworkXNoPath:
            raise ValueError(f"{start}에서 {end}까지의 경로를 찾을 수 없습니다.")
        except Exception as e:
            raise ValueError(f"경로 계산 중 오류가 발생했습니다: {str(e)}")

    def calculate_distance(self, loc1: Location, loc2: Location) -> float:
        """두 위치 간의 유클리드 거리 계산
        Args:
            loc1 (Location): 첫 번째 위치
            loc2 (Location): 두 번째 위치
        Returns:
            float: 두 위치 간의 거리
        """
        return math.sqrt((loc1.x_coord - loc2.x_coord) ** 2 + (loc1.y_coord - loc2.y_coord) ** 2)

    def find_nearest_location(self, current_loc: Location, target_locations: List[Location]) -> Location:
        """현재 위치에서 가장 가까운 위치 찾기
        Args:
            current_loc (Location): 현재 위치
            target_locations (List[Location]): 대상 위치 목록
        Returns:
            Location: 가장 가까운 위치
        """
        if not target_locations:
            return None
        
        return min(target_locations, key=lambda loc: self.calculate_distance(current_loc, loc))

    def optimize_route(self, start_location: Location, target_locations: List[Location]) -> List[Location]:
        """최근접 이웃 알고리즘을 사용한 경로 최적화
        Args:
            start_location (Location): 시작 위치
            target_locations (List[Location]): 방문할 위치 목록
        Returns:
            List[Location]: 최적화된 경로
        """
        if not target_locations:
            return []

        route = []
        current_loc = start_location
        remaining_locations = target_locations.copy()

        while remaining_locations:
            next_loc = self.find_nearest_location(current_loc, remaining_locations)
            route.append(next_loc)
            remaining_locations.remove(next_loc)
            current_loc = next_loc

        return route 