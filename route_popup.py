import customtkinter as ctk
import pandas as pd
import networkx as nx
from typing import List, Dict, Union

class RoutePopup(ctk.CTkToplevel):
    def __init__(self, parent, locations: Union[pd.DataFrame, List[Dict]]):
        super().__init__(parent)
        self.title("경유 경로 안내")
        self.geometry("400x500")
        
        # DataFrame이 아닌 경우 DataFrame으로 변환
        if not isinstance(locations, pd.DataFrame):
            self.locations_df = pd.DataFrame(locations)
        else:
            self.locations_df = locations
            
        # elevator 컬럼이 없는 경우 추가 (기본값 0)
        if 'elevator' not in self.locations_df.columns:
            self.locations_df['elevator'] = 0
            
        self.G = self.create_graph()
        
        # 클래스 선택
        self.class_label = ctk.CTkLabel(self, text="클래스 선택:")
        self.class_label.pack(pady=5)
        self.class_var = ctk.StringVar(value="1-1")
        self.class_combo = ctk.CTkComboBox(self, values=["1-1", "1-2", "1-3", "1-4", "1-5", "1-6", "1-7", "1-8", "1-9", "1-10", "1-11", "1-12"], variable=self.class_var)
        self.class_combo.pack(pady=5)
        
        # 요일 선택
        self.day_label = ctk.CTkLabel(self, text="요일 선택:")
        self.day_label.pack(pady=5)
        self.day_var = ctk.StringVar(value="월")
        self.day_combo = ctk.CTkComboBox(self, values=["월", "화", "수", "목", "금"], variable=self.day_var)
        self.day_combo.pack(pady=5)
        
        # 교시 선택
        self.period_label = ctk.CTkLabel(self, text="교시 선택:")
        self.period_label.pack(pady=5)
        self.period_var = ctk.StringVar(value="1")
        self.period_combo = ctk.CTkComboBox(self, values=["1", "2", "3", "4", "5", "6", "7", "8", "9"], variable=self.period_var)
        self.period_combo.pack(pady=5)
        
        # 목적지 선택
        self.dest_label = ctk.CTkLabel(self, text="목적지 선택:")
        self.dest_label.pack(pady=5)
        self.dest_var = ctk.StringVar(value="매점")
        self.dest_combo = ctk.CTkComboBox(self, values=["매점", "기숙사"], variable=self.dest_var)
        self.dest_combo.pack(pady=5)
        
        # 다리 부상 체크박스
        self.leg_injury_var = ctk.BooleanVar(value=False)
        self.leg_injury_check = ctk.CTkCheckBox(self, text="다리 부상", variable=self.leg_injury_var)
        self.leg_injury_check.pack(pady=5)
        
        # 경로 안내 버튼
        self.route_button = ctk.CTkButton(self, text="경로 안내", command=self.show_route)
        self.route_button.pack(pady=10)
        
        # 경로 표시 텍스트
        self.route_text = ctk.CTkTextbox(self, width=350, height=200)
        self.route_text.pack(pady=10, padx=10)
        
    def create_graph(self) -> nx.Graph:
        G = nx.Graph()
        
        # 노드 추가
        for _, row in self.locations_df.iterrows():
            G.add_node(row['room_number'], 
                      pos=(row['x_coord'], row['y_coord']),
                      building=row['building'],
                      floor=row['floor'],
                      elevator=row['elevator'])
        
        # 엣지 추가 (같은 건물, 같은 층 내 연결)
        for i, row1 in self.locations_df.iterrows():
            for j, row2 in self.locations_df.iterrows():
                if i < j and row1['building'] == row2['building'] and row1['floor'] == row2['floor']:
                    # 거리 계산
                    dist = ((row1['x_coord'] - row2['x_coord'])**2 + 
                           (row1['y_coord'] - row2['y_coord'])**2)**0.5
                    G.add_edge(row1['room_number'], row2['room_number'], 
                             weight=dist)
        
        # 건물 간 연결 (엘리베이터가 있는 건물만)
        buildings_with_elevator = self.locations_df[self.locations_df['elevator'] == 1]['building'].unique()
        for building in buildings_with_elevator:
            building_rooms = self.locations_df[self.locations_df['building'] == building]['room_number'].tolist()
            for room1 in building_rooms:
                for room2 in building_rooms:
                    if room1 != room2:
                        floor1 = self.locations_df[self.locations_df['room_number'] == room1]['floor'].iloc[0]
                        floor2 = self.locations_df[self.locations_df['room_number'] == room2]['floor'].iloc[0]
                        if abs(floor1 - floor2) == 1:  # 인접한 층만 연결
                            G.add_edge(room1, room2, weight=20)  # 층 이동 가중치
        
        return G
    
    def show_route(self):
        try:
            class_name = self.class_var.get()
            day = self.day_var.get()
            period = int(self.period_var.get())
            destination = self.dest_var.get()
            use_elevator = self.leg_injury_var.get()
            
            # 현재 교실 찾기
            current_classroom = None
            for _, row in self.locations_df.iterrows():
                if row['room_number'].startswith(class_name):
                    current_classroom = row['room_number']
                    break
            
            if not current_classroom:
                self.route_text.delete("1.0", "end")
                self.route_text.insert("1.0", "현재 교실을 찾을 수 없습니다.")
                return
            
            # 경로 찾기
            try:
                if use_elevator:
                    # 엘리베이터를 포함한 경로 찾기
                    path = self.find_elevator_path(current_classroom, destination)
                else:
                    # 일반 최단 경로 찾기
                    path = nx.shortest_path(self.G, current_classroom, destination, weight='weight')
                
                # 경로 텍스트 생성
                route_text = f"추천 경로:\n"
                for i in range(len(path)-1):
                    current = path[i]
                    next_node = path[i+1]
                    current_info = self.locations_df[self.locations_df['room_number'] == current].iloc[0]
                    next_info = self.locations_df[self.locations_df['room_number'] == next_node].iloc[0]
                    
                    if current_info['building'] != next_info['building']:
                        route_text += f"{current}({current_info['building']}) → {next_node}({next_info['building']}) (건물 이동)\n"
                    elif current_info['floor'] != next_info['floor']:
                        route_text += f"{current}({current_info['building']} {current_info['floor']}층) → {next_node}({next_info['building']} {next_info['floor']}층) (층 이동)\n"
                    else:
                        route_text += f"{current}({current_info['building']} {current_info['floor']}층) → {next_node}({next_info['building']} {next_info['floor']}층)\n"
                
                self.route_text.delete("1.0", "end")
                self.route_text.insert("1.0", route_text)
                
            except nx.NetworkXNoPath:
                self.route_text.delete("1.0", "end")
                if use_elevator:
                    self.route_text.insert("1.0", "엘리베이터를 포함한 경로를 찾을 수 없습니다.")
                else:
                    self.route_text.insert("1.0", "경로를 찾을 수 없습니다.")
                
        except Exception as e:
            self.route_text.delete("1.0", "end")
            self.route_text.insert("1.0", f"오류 발생: {str(e)}")
    
    def find_elevator_path(self, start: str, end: str) -> List[str]:
        """엘리베이터를 포함한 경로 찾기"""
        # 시작점과 도착점의 건물과 층 확인
        start_info = self.locations_df[self.locations_df['room_number'] == start].iloc[0]
        end_info = self.locations_df[self.locations_df['room_number'] == end].iloc[0]
        
        if start_info['building'] == end_info['building'] and start_info['floor'] == end_info['floor']:
            # 같은 건물, 같은 층이면 일반 최단 경로 사용
            return nx.shortest_path(self.G, start, end, weight='weight')
        
        # 엘리베이터가 있는 건물 찾기
        buildings_with_elevator = self.locations_df[self.locations_df['elevator'] == 1]['building'].unique()
        if len(buildings_with_elevator) == 0:
            raise nx.NetworkXNoPath("엘리베이터가 있는 건물이 없습니다.")
        
        # 시작점에서 가장 가까운 엘리베이터가 있는 건물 찾기
        start_building = start_info['building']
        if start_building not in buildings_with_elevator:
            # 시작 건물에 엘리베이터가 없으면 가장 가까운 엘리베이터가 있는 건물로 이동
            closest_building = min(buildings_with_elevator, 
                                 key=lambda b: abs(self.locations_df[self.locations_df['building'] == b]['x_coord'].mean() - 
                                                  self.locations_df[self.locations_df['building'] == start_building]['x_coord'].mean()))
            # 시작점에서 가장 가까운 엘리베이터가 있는 건물의 입구로 이동
            building_entrance = self.locations_df[
                (self.locations_df['building'] == closest_building) & 
                (self.locations_df['floor'] == 1)
            ]['room_number'].iloc[0]
            path1 = nx.shortest_path(self.G, start, building_entrance, weight='weight')
        else:
            path1 = [start]
        
        # 도착점에서 가장 가까운 엘리베이터가 있는 건물 찾기
        end_building = end_info['building']
        if end_building not in buildings_with_elevator:
            # 도착 건물에 엘리베이터가 없으면 가장 가까운 엘리베이터가 있는 건물로 이동
            closest_building = min(buildings_with_elevator, 
                                 key=lambda b: abs(self.locations_df[self.locations_df['building'] == b]['x_coord'].mean() - 
                                                  self.locations_df[self.locations_df['building'] == end_building]['x_coord'].mean()))
            # 도착점에서 가장 가까운 엘리베이터가 있는 건물의 입구로 이동
            building_entrance = self.locations_df[
                (self.locations_df['building'] == closest_building) & 
                (self.locations_df['floor'] == 1)
            ]['room_number'].iloc[0]
            path3 = nx.shortest_path(self.G, building_entrance, end, weight='weight')
        else:
            path3 = [end]
        
        # 중간 경로 찾기
        if len(path1) > 1 and len(path3) > 1:
            path2 = nx.shortest_path(self.G, path1[-1], path3[0], weight='weight')
            return path1[:-1] + path2[:-1] + path3
        elif len(path1) > 1:
            return path1[:-1] + path3
        elif len(path3) > 1:
            return path1 + path3
        else:
            return nx.shortest_path(self.G, start, end, weight='weight') 