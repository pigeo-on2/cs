# 필요한 라이브러리 임포트
import networkx as nx

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