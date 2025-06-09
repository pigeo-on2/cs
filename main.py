from data_loader import DataLoader
from scheduler import Scheduler
from graph_util import build_graph, shortest_path
from gui import AppGUI
from models import Location
import customtkinter as ctk
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.font_manager as fm
import os
from typing import List, Dict, Optional, Union
from dataclasses import dataclass
import random
from datetime import datetime
import json
import tkinter.messagebox as messagebox

class RouteOptimizer:
    def __init__(self, locations: Union[pd.DataFrame, List[Dict]]):
        self.graph = self.create_graph(locations)
    
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

class AppGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Initialize components
        self.loader = DataLoader()
        self.scheduler = TimetableScheduler(self.loader)
        self.route_opt = RouteOptimizer(self.loader)
        
        self.title("시간표 및 경로 최적화")
        self.geometry("800x600")
        
        # Create main frame with scrollbar
        self.main_frame = ctk.CTkScrollableFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create tabs
        self.tabview = ctk.CTkTabview(self.main_frame)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Add tabs
        self.tabview.add("시간표 관리")
        self.tabview.add("경로 안내")
        
        # Initialize tab contents
        self.init_timetable_tab()
        self.init_route_tab()
        
    def init_timetable_tab(self):
        tab = self.tabview.tab("시간표 관리")
        
        # Class selection
        self.class_label = ctk.CTkLabel(tab, text="클래스 선택:")
        self.class_label.pack(pady=5)
        self.class_var = ctk.StringVar(value="1-1")
        self.class_combo = ctk.CTkComboBox(tab, values=["1-1", "1-2", "1-3", "1-4", "1-5", "1-6", "1-7", "1-8", "1-9", "1-10", "1-11", "1-12"], variable=self.class_var)
        self.class_combo.pack(pady=5)
        
        # Generate timetable button
        self.generate_button = ctk.CTkButton(tab, text="시간표 생성", command=self.generate_timetable)
        self.generate_button.pack(pady=10)
        
        # View timetable button
        self.view_button = ctk.CTkButton(tab, text="시간표 보기", command=self.view_timetable)
        self.view_button.pack(pady=10)
        
    def init_route_tab(self):
        tab = self.tabview.tab("경로 안내")
        
        # Route guidance button
        self.route_button = ctk.CTkButton(tab, text="경로 안내", command=self.show_route)
        self.route_button.pack(pady=10)
        
    def generate_timetable(self):
        class_name = self.class_var.get()
        try:
            self.scheduler.generate_timetable(class_name)
            messagebox.showinfo("성공", f"{class_name} 시간표가 생성되었습니다.")
        except Exception as e:
            messagebox.showerror("오류", str(e))
            
    def view_timetable(self):
        class_name = self.class_var.get()
        try:
            timetable = self.scheduler.get_timetable(class_name)
            if timetable is None:
                messagebox.showwarning("경고", "먼저 시간표를 생성해주세요.")
                return
                
            TimetablePopup(self, timetable)
        except Exception as e:
            messagebox.showerror("오류", str(e))
            
    def show_route(self):
        try:
            locations = self.loader.get_locations()
            if locations is None:
                messagebox.showerror("오류", "위치 정보를 불러올 수 없습니다.")
                return
                
            RoutePopup(self, locations)
        except Exception as e:
            messagebox.showerror("오류", str(e))

if __name__ == "__main__":
    app = AppGUI()
    app.mainloop()

