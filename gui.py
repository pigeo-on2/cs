import customtkinter as ctk
from visualizer import plot_timetable, plot_route
from data_manager_gui import DataManagerGUI
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.font_manager as fm
import os
from typing import List, Dict, Optional
from dataclasses import dataclass
import random
from datetime import datetime
import json

class AppGUI(ctk.CTk):
    def __init__(self, scheduler, route_opt, loader):
        super().__init__()
        
        # Configure window
        self.title('Minimal Move Timetable')
        self.geometry("800x600")
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Set theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        self.scheduler = scheduler
        self.route_opt = route_opt
        self.loader = loader
        
        self.selected_class = None
        self.timetables = None
        self.class_dropdown = None
        self.timetable_text = None
        
        # Create tabview
        self.tabview = ctk.CTkTabview(self)
        self.tabview.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        
        # Create tabs
        self.tab_main = self.tabview.add("메인")
        self.tab_data = self.tabview.add("데이터 관리")
        self.tab_route = self.tabview.add("장애인 경로 안내")
        
        self.create_main_tab()
        self.create_route_tab()
        
        # Create data manager GUI
        self.data_manager = DataManagerGUI(self.tab_data, loader)

    def create_main_tab(self):
        # 스크롤 가능한 프레임 생성
        self.scroll_frame = ctk.CTkScrollableFrame(self.tab_main, width=760, height=550)
        self.scroll_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.tab_main.grid_rowconfigure(0, weight=1)
        self.tab_main.grid_columnconfigure(0, weight=1)
        # Title label
        self.title_label = ctk.CTkLabel(
            self.scroll_frame,
            text="시간표 및 경로 최적화",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.title_label.pack(pady=(20, 10))
        # Buttons
        self.timetable_btn = ctk.CTkButton(
            self.scroll_frame,
            text="시간표 생성 및 시각화",
            command=self.show_timetable,
            height=40
        )
        self.timetable_btn.pack(pady=10, fill="x")
        self.class_dropdown = ctk.CTkComboBox(
            self.scroll_frame,
            values=[],
            command=self.on_class_select
        )
        self.class_dropdown.pack(pady=10, fill="x")
        self.timetable_text = ctk.CTkTextbox(self.scroll_frame, width=600, height=300)
        self.timetable_text.pack(pady=10, fill="both", expand=True)
        self.visualize_btn = ctk.CTkButton(
            self.scroll_frame,
            text="선택 반 시간표 이미지로 시각화",
            command=self.visualize_selected_timetable,
            height=40
        )
        self.visualize_btn.pack(pady=10, fill="x")

    def create_route_tab(self):
        # 스크롤 가능한 프레임 생성
        self.route_scroll_frame = ctk.CTkScrollableFrame(self.tab_route, width=760, height=550)
        self.route_scroll_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.tab_route.grid_rowconfigure(0, weight=1)
        self.tab_route.grid_columnconfigure(0, weight=1)

        # Title label
        self.route_title_label = ctk.CTkLabel(
            self.route_scroll_frame,
            text="장애인 이동 경로 안내",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.route_title_label.pack(pady=(20, 10))

        # 반 선택
        self.route_class_label = ctk.CTkLabel(
            self.route_scroll_frame,
            text="반 선택:",
            font=ctk.CTkFont(size=14)
        )
        self.route_class_label.pack(pady=(10, 5))
        self.route_class_dropdown = ctk.CTkComboBox(
            self.route_scroll_frame,
            values=[],
            command=self.on_route_class_select
        )
        self.route_class_dropdown.pack(pady=5, fill="x")

        # 요일 선택
        self.day_label = ctk.CTkLabel(
            self.route_scroll_frame,
            text="요일 선택:",
            font=ctk.CTkFont(size=14)
        )
        self.day_label.pack(pady=(10, 5))
        self.day_dropdown = ctk.CTkComboBox(
            self.route_scroll_frame,
            values=['월요일', '화요일', '수요일', '목요일', '금요일']
        )
        self.day_dropdown.pack(pady=5, fill="x")

        # 교시 선택
        self.period_label = ctk.CTkLabel(
            self.route_scroll_frame,
            text="교시 선택:",
            font=ctk.CTkFont(size=14)
        )
        self.period_label.pack(pady=(10, 5))
        self.period_dropdown = ctk.CTkComboBox(
            self.route_scroll_frame,
            values=['1', '2', '3', '4', '5', '6', '7']
        )
        self.period_dropdown.pack(pady=5, fill="x")

        # 목적지 선택
        self.destination_label = ctk.CTkLabel(
            self.route_scroll_frame,
            text="목적지 선택:",
            font=ctk.CTkFont(size=14)
        )
        self.destination_label.pack(pady=(10, 5))
        self.destination_dropdown = ctk.CTkComboBox(
            self.route_scroll_frame,
            values=['매점', '기숙사']
        )
        self.destination_dropdown.pack(pady=5, fill="x")

        # 경로 생성 버튼
        self.generate_route_btn = ctk.CTkButton(
            self.route_scroll_frame,
            text="경로 생성",
            command=self.generate_route,
            height=40
        )
        self.generate_route_btn.pack(pady=20, fill="x")

        # 경로 표시 텍스트 박스
        self.route_text = ctk.CTkTextbox(
            self.route_scroll_frame,
            width=600,
            height=200
        )
        self.route_text.pack(pady=10, fill="both", expand=True)

    def show_timetable(self):
        self.timetables = self.scheduler.generate()
        class_list = sorted(self.timetables.keys(), key=lambda x: int(x) if x.isdigit() else x)
        self.class_dropdown.configure(values=class_list)
        if class_list:
            self.class_dropdown.set(class_list[0])
            self.display_timetable(class_list[0])

    def on_class_select(self, selected_class):
        self.display_timetable(selected_class)

    def display_timetable(self, class_num):
        timetable = self.timetables.get(class_num)
        if not timetable:
            self.timetable_text.delete("1.0", "end")
            self.timetable_text.insert("end", f"{class_num}반 시간표가 없습니다.")
            return
        days = ['월요일', '화요일', '수요일', '목요일', '금요일']
        periods = [1,2,3,4,5,6,7]
        text = f"[{class_num}반 시간표]\n"
        for day in days:
            text += f"{day}:\n"
            for i, entry in enumerate(timetable[day]):
                if entry:
                    text += f"  {i+1}교시: {entry['과목']} ({entry['선생님']}, {entry['교실']})\n"
                else:
                    text += f"  {i+1}교시: -\n"
        self.timetable_text.delete("1.0", "end")
        self.timetable_text.insert("end", text)

    def visualize_selected_timetable(self):
        class_num = self.class_dropdown.get()
        if not class_num or not self.timetables or class_num not in self.timetables:
            print("No timetable or class selected")
            return
        timetable = self.timetables[class_num]
        save_path = f"{class_num}반_시간표.png"
        try:
            print(f"시각화 시도: {class_num}, {save_path}")
            print(f"graph is None? {self.scheduler.graph is None}")
            from visualizer import plot_timetable
            plot_timetable(
                timetable,
                class_name=class_num,
                graph=self.scheduler.graph,
                save_path=save_path
            )
            print("시각화 완료")
        except Exception as e:
            print(f"시각화 중 오류: {e}")

    def on_route_class_select(self, selected_class):
        self.selected_class = selected_class
        if self.timetables:
            self.display_timetable(selected_class)

    def generate_route(self):
        class_num = self.route_class_dropdown.get()
        day = self.day_dropdown.get()
        period = int(self.period_dropdown.get())
        destination = self.destination_dropdown.get()

        if not class_num or not self.timetables or class_num not in self.timetables:
            self.route_text.delete("1.0", "end")
            self.route_text.insert("end", "시간표를 먼저 생성해주세요.")
            return

        timetable = self.timetables[class_num]
        current_location = None
        if timetable[day][period-1]:
            current_location = timetable[day][period-1]['교실']
        else:
            self.route_text.delete("1.0", "end")
            self.route_text.insert("end", f"{period}교시에 수업이 없습니다.")
            return

        try:
            path = self.route_opt.shortest_path(current_location, destination)
            route_text = f"현재 위치: {current_location}\n"
            route_text += f"목적지: {destination}\n\n"
            route_text += "이동 경로:\n"
            for i, location in enumerate(path, 1):
                route_text += f"{i}. {location}\n"
            
            self.route_text.delete("1.0", "end")
            self.route_text.insert("end", route_text)
        except Exception as e:
            self.route_text.delete("1.0", "end")
            self.route_text.insert("end", f"경로 생성 중 오류가 발생했습니다: {str(e)}")
            