from typing import List, Dict, Union
import pandas as pd
import networkx as nx
import math
from models import Location

class RouteOptimizer:
    def __init__(self, loader):
        self.locations = loader.load_locations()
        self.graph = self.create_graph(self.locations)

    def create_graph(self, locations: Union[pd.DataFrame, List[Dict]]) -> nx.Graph:
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
        
        return G
    
    def shortest_path(self, start: str, end: str) -> List[str]:
        return nx.shortest_path(self.graph, start, end, weight='weight')

    def calculate_distance(self, loc1: Location, loc2: Location) -> float:
        """Calculate the Euclidean distance between two locations"""
        return math.sqrt((loc1.x_coord - loc2.x_coord) ** 2 + (loc1.y_coord - loc2.y_coord) ** 2)

    def find_nearest_location(self, current_loc: Location, target_locations: List[Location]) -> Location:
        """Find the nearest location from the current location"""
        if not target_locations:
            return None
        
        return min(target_locations, key=lambda loc: self.calculate_distance(current_loc, loc))

    def optimize_route(self, start_location: Location, target_locations: List[Location]) -> List[Location]:
        """Optimize the route using a simple nearest neighbor algorithm"""
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