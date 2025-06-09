import networkx as nx

def build_graph(locations):
    """
    locations: List[Location] - List of Location objects
    거리+계단수 가중치로 완전 연결 그래프 생성
    """
    G = nx.Graph()
    for loc in locations:
        G.add_node(loc.room_number, 
                  building=loc.building,
                  floor=loc.floor,
                  x_coord=loc.x_coord,
                  y_coord=loc.y_coord)
    for i, a in enumerate(locations):
        for b in locations[i+1:]:
            dist = ((a.x_coord-b.x_coord)**2 + (a.y_coord-b.y_coord)**2)**0.5
            stairs = abs(a.floor-b.floor)
            weight = dist + stairs * 5  # 계단 가중치(예시)
            G.add_edge(a.room_number, b.room_number, weight=weight)
    return G

def shortest_path(G, start, end):
    """최단 경로(가중치 기준) 반환"""
    return nx.shortest_path(G, start, end, weight='weight') 