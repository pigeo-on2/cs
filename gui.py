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
import pygame
from PIL import Image
import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                           QHBoxLayout, QPushButton, QLabel, QComboBox,
                           QSpinBox, QDoubleSpinBox, QCheckBox, QGroupBox,
                           QMessageBox, QTabWidget, QTextEdit, QFileDialog)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont
import logging

# 로거 설정
logger = logging.getLogger(__name__)

class AppGUI(ctk.CTk):
    """메인 GUI 애플리케이션 클래스"""
    def __init__(self, scheduler, route_opt, loader):
        """GUI 초기화
        Args:
            scheduler: 스케줄러 객체
            route_opt: 경로 최적화 객체
            loader: 데이터 로더 객체
        """
        super().__init__()
        
        # 윈도우 설정
        self.title('Minimal Move Timetable')
        self.geometry("800x600")
        
        # 그리드 설정
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # 테마 설정
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        self.scheduler = scheduler
        self.route_opt = route_opt
        self.loader = loader
        
        self.selected_class = None
        self.timetables = None
        self.class_dropdown = None
        self.timetable_text = None
        
        # 탭뷰 생성
        self.tabview = ctk.CTkTabview(self)
        self.tabview.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        
        # 탭 생성
        self.tab_main = self.tabview.add("메인")
        self.tab_data = self.tabview.add("데이터 관리")
        self.tab_route = self.tabview.add("경로 최적화")
        
        self.create_main_tab()
        self.create_route_tab()
        
        # 데이터 관리 GUI 생성
        self.data_manager = DataManagerGUI(self.tab_data, loader)
        
        # 왼쪽 상단에 로고 이미지 삽입
        logo_img = Image.open("data/icon.png").resize((32, 32))
        self.logo_photo = ctk.CTkImage(light_image=logo_img, dark_image=logo_img, size=(32, 32))
        self.logo_label = ctk.CTkLabel(self, image=self.logo_photo, text="")
        self.logo_label.place(x=10, y=10)

    def create_main_tab(self):
        """메인 탭 생성"""
        # 스크롤 가능한 프레임 생성
        self.scroll_frame = ctk.CTkScrollableFrame(self.tab_main, width=760, height=550)
        self.scroll_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.tab_main.grid_rowconfigure(0, weight=1)
        self.tab_main.grid_columnconfigure(0, weight=1)
        
        # 제목 레이블
        self.title_label = ctk.CTkLabel(
            self.scroll_frame,
            text="시간표 및 경로 최적화",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.title_label.pack(pady=(20, 10))
        
        # 버튼들
        self.timetable_btn = ctk.CTkButton(
            self.scroll_frame,
            text="시간표 생성 및 시각화",
            command=self.show_timetable,
            height=40
        )
        self.timetable_btn.pack(pady=10, fill="x")
        
        # 반 선택 드롭다운
        self.class_dropdown = ctk.CTkComboBox(
            self.scroll_frame,
            values=[],
            command=self.on_class_select
        )
        self.class_dropdown.pack(pady=10, fill="x")
        
        # 시간표 텍스트 박스
        self.timetable_text = ctk.CTkTextbox(self.scroll_frame, width=600, height=300)
        self.timetable_text.pack(pady=10, fill="both", expand=True)
        
        # 시각화 버튼
        self.visualize_btn = ctk.CTkButton(
            self.scroll_frame,
            text="선택 반 시간표 이미지로 시각화",
            command=self.visualize_selected_timetable,
            height=40
        )
        self.visualize_btn.pack(pady=10, fill="x")

    def create_route_tab(self):
        """경로 최적화 탭 생성"""
        # 스크롤 가능한 프레임 생성
        self.route_scroll_frame = ctk.CTkScrollableFrame(self.tab_route, width=760, height=550)
        self.route_scroll_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.tab_route.grid_rowconfigure(0, weight=1)
        self.tab_route.grid_columnconfigure(0, weight=1)

        # 제목 레이블
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
        """시간표 생성 및 표시"""
        self.timetables = self.scheduler.generate()
        class_list = sorted(self.timetables.keys(), key=lambda x: int(x) if x.isdigit() else x)
        self.class_dropdown.configure(values=class_list)
        if class_list:
            self.class_dropdown.set(class_list[0])
            self.display_timetable(class_list[0])
        # 시간표 완성 시 알람
        try:
            pygame.mixer.music.load("data/alarm.mp3")
            pygame.mixer.music.play()
        except Exception as e:
            print(f"Alarm sound error: {e}")

    def on_class_select(self, selected_class):
        """반 선택 시 호출되는 콜백 함수"""
        self.display_timetable(selected_class)

    def display_timetable(self, class_num):
        """시간표 표시
        Args:
            class_num (str): 반 번호
        """
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
        """선택된 시간표 시각화"""
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
        """경로 최적화 탭에서 반 선택 시 호출되는 콜백 함수"""
        self.selected_class = selected_class
        if self.timetables:
            self.display_timetable(selected_class)

    def generate_route(self):
        """경로 생성"""
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
            # 경로 생성 성공 시 알람
            try:
                pygame.mixer.music.load("data/alarm.mp3")
                pygame.mixer.music.play()
            except Exception as e:
                print(f"Alarm sound error: {e}")
        except Exception as e:
            self.route_text.delete("1.0", "end")
            self.route_text.insert("end", f"경로 생성 중 오류가 발생했습니다: {str(e)}")
            
class MainWindow(QMainWindow):
    """
    메인 윈도우 클래스
    
    이 클래스는 애플리케이션의 메인 윈도우를 구현하며,
    사용자 인터페이스의 주요 구성 요소를 포함합니다.
    """
    
    def __init__(self):
        """MainWindow 초기화"""
        super().__init__()
        self.init_ui()
        self.setup_connections()
        self.setup_timer()
        
    def init_ui(self):
        """사용자 인터페이스 초기화"""
        # 메인 윈도우 설정
        self.setWindowTitle('배송 최적화 시스템')
        self.setGeometry(100, 100, 1200, 800)
        
        # 중앙 위젯 생성
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 메인 레이아웃 설정
        layout = QVBoxLayout(central_widget)
        
        # 탭 위젯 생성
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # 각 탭 생성
        self.create_control_tab()
        self.create_settings_tab()
        self.create_monitoring_tab()
        self.create_log_tab()
        
        # 상태 표시줄 생성
        self.statusBar().showMessage('준비')
        
    def create_control_tab(self):
        """제어 탭 생성"""
        control_tab = QWidget()
        layout = QVBoxLayout(control_tab)
        
        # 제어 버튼 그룹
        control_group = QGroupBox('시스템 제어')
        control_layout = QHBoxLayout()
        
        # 시작 버튼
        self.start_button = QPushButton('시작')
        self.start_button.setStyleSheet('background-color: #4CAF50; color: white;')
        control_layout.addWidget(self.start_button)
        
        # 중지 버튼
        self.stop_button = QPushButton('중지')
        self.stop_button.setStyleSheet('background-color: #f44336; color: white;')
        control_layout.addWidget(self.stop_button)
        
        # 일시정지 버튼
        self.pause_button = QPushButton('일시정지')
        self.pause_button.setStyleSheet('background-color: #FFC107; color: black;')
        control_layout.addWidget(self.pause_button)
        
        control_group.setLayout(control_layout)
        layout.addWidget(control_group)
        
        # 상태 표시 그룹
        status_group = QGroupBox('시스템 상태')
        status_layout = QVBoxLayout()
        
        # 상태 레이블
        self.status_label = QLabel('대기 중')
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setFont(QFont('Arial', 14, QFont.Bold))
        status_layout.addWidget(self.status_label)
        
        # 진행률 표시
        self.progress_label = QLabel('0%')
        self.progress_label.setAlignment(Qt.AlignCenter)
        status_layout.addWidget(self.progress_label)
        
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
        # 탭에 추가
        self.tabs.addTab(control_tab, '제어')
        
    def create_settings_tab(self):
        """설정 탭 생성"""
        settings_tab = QWidget()
        layout = QVBoxLayout(settings_tab)
        
        # 최적화 설정 그룹
        optimization_group = QGroupBox('최적화 설정')
        optimization_layout = QVBoxLayout()
        
        # 알고리즘 선택
        algorithm_layout = QHBoxLayout()
        algorithm_layout.addWidget(QLabel('알고리즘:'))
        self.algorithm_combo = QComboBox()
        self.algorithm_combo.addItems(['탐욕 알고리즘', '유전 알고리즘', '시뮬레이티드 어닐링'])
        algorithm_layout.addWidget(self.algorithm_combo)
        optimization_layout.addLayout(algorithm_layout)
        
        # 반복 횟수 설정
        iterations_layout = QHBoxLayout()
        iterations_layout.addWidget(QLabel('반복 횟수:'))
        self.iterations_spin = QSpinBox()
        self.iterations_spin.setRange(1, 1000)
        self.iterations_spin.setValue(100)
        iterations_layout.addWidget(self.iterations_spin)
        optimization_layout.addLayout(iterations_layout)
        
        # 시간 제한 설정
        time_limit_layout = QHBoxLayout()
        time_limit_layout.addWidget(QLabel('시간 제한(초):'))
        self.time_limit_spin = QSpinBox()
        self.time_limit_spin.setRange(1, 3600)
        self.time_limit_spin.setValue(300)
        time_limit_layout.addWidget(self.time_limit_spin)
        optimization_layout.addLayout(time_limit_layout)
        
        optimization_group.setLayout(optimization_layout)
        layout.addWidget(optimization_group)
        
        # 제약 조건 설정 그룹
        constraints_group = QGroupBox('제약 조건')
        constraints_layout = QVBoxLayout()
        
        # 시간 제약 활성화
        self.time_constraint_check = QCheckBox('시간 제약 사용')
        self.time_constraint_check.setChecked(True)
        constraints_layout.addWidget(self.time_constraint_check)
        
        # 용량 제약 활성화
        self.capacity_constraint_check = QCheckBox('용량 제약 사용')
        self.capacity_constraint_check.setChecked(True)
        constraints_layout.addWidget(self.capacity_constraint_check)
        
        # 우선순위 활성화
        self.priority_check = QCheckBox('우선순위 사용')
        self.priority_check.setChecked(True)
        constraints_layout.addWidget(self.priority_check)
        
        constraints_group.setLayout(constraints_layout)
        layout.addWidget(constraints_group)
        
        # 설정 저장 버튼
        self.save_settings_button = QPushButton('설정 저장')
        layout.addWidget(self.save_settings_button)
        
        # 탭에 추가
        self.tabs.addTab(settings_tab, '설정')
        
    def create_monitoring_tab(self):
        """모니터링 탭 생성"""
        monitoring_tab = QWidget()
        layout = QVBoxLayout(monitoring_tab)
        
        # 성능 지표 그룹
        metrics_group = QGroupBox('성능 지표')
        metrics_layout = QVBoxLayout()
        
        # 현재 비용
        cost_layout = QHBoxLayout()
        cost_layout.addWidget(QLabel('현재 비용:'))
        self.cost_label = QLabel('0')
        cost_layout.addWidget(self.cost_label)
        metrics_layout.addLayout(cost_layout)
        
        # 현재 거리
        distance_layout = QHBoxLayout()
        distance_layout.addWidget(QLabel('현재 거리:'))
        self.distance_label = QLabel('0')
        distance_layout.addWidget(self.distance_label)
        metrics_layout.addLayout(distance_layout)
        
        # 현재 시간
        time_layout = QHBoxLayout()
        time_layout.addWidget(QLabel('현재 시간:'))
        self.time_label = QLabel('0')
        time_layout.addWidget(self.time_label)
        metrics_layout.addLayout(time_layout)
        
        metrics_group.setLayout(metrics_layout)
        layout.addWidget(metrics_group)
        
        # 그래프 표시 영역
        self.graph_label = QLabel('그래프가 여기에 표시됩니다.')
        self.graph_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.graph_label)
        
        # 탭에 추가
        self.tabs.addTab(monitoring_tab, '모니터링')
        
    def create_log_tab(self):
        """로그 탭 생성"""
        log_tab = QWidget()
        layout = QVBoxLayout(log_tab)
        
        # 로그 표시 영역
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)
        
        # 로그 제어 버튼
        log_control_layout = QHBoxLayout()
        
        # 로그 저장 버튼
        self.save_log_button = QPushButton('로그 저장')
        log_control_layout.addWidget(self.save_log_button)
        
        # 로그 지우기 버튼
        self.clear_log_button = QPushButton('로그 지우기')
        log_control_layout.addWidget(self.clear_log_button)
        
        layout.addLayout(log_control_layout)
        
        # 탭에 추가
        self.tabs.addTab(log_tab, '로그')
        
    def setup_connections(self):
        """이벤트 핸들러 연결"""
        # 제어 버튼
        self.start_button.clicked.connect(self.start_system)
        self.stop_button.clicked.connect(self.stop_system)
        self.pause_button.clicked.connect(self.pause_system)
        
        # 설정 버튼
        self.save_settings_button.clicked.connect(self.save_settings)
        
        # 로그 버튼
        self.save_log_button.clicked.connect(self.save_log)
        self.clear_log_button.clicked.connect(self.clear_log)
        
    def setup_timer(self):
        """타이머 설정"""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_status)
        self.update_timer.start(1000)  # 1초마다 업데이트
        
    def start_system(self):
        """시스템 시작"""
        try:
            self.status_label.setText('실행 중')
            self.status_label.setStyleSheet('color: #4CAF50;')
            self.log_message('시스템이 시작되었습니다.')
            logger.info("시스템 시작")
            
        except Exception as e:
            self.log_message(f'시스템 시작 중 오류 발생: {str(e)}')
            logger.error(f"시스템 시작 중 오류 발생: {str(e)}")
            
    def stop_system(self):
        """시스템 중지"""
        try:
            self.status_label.setText('중지됨')
            self.status_label.setStyleSheet('color: #f44336;')
            self.log_message('시스템이 중지되었습니다.')
            logger.info("시스템 중지")
            
        except Exception as e:
            self.log_message(f'시스템 중지 중 오류 발생: {str(e)}')
            logger.error(f"시스템 중지 중 오류 발생: {str(e)}")
            
    def pause_system(self):
        """시스템 일시정지"""
        try:
            if self.status_label.text() == '일시정지':
                self.status_label.setText('실행 중')
                self.status_label.setStyleSheet('color: #4CAF50;')
                self.log_message('시스템이 재개되었습니다.')
                logger.info("시스템 재개")
            else:
                self.status_label.setText('일시정지')
                self.status_label.setStyleSheet('color: #FFC107;')
                self.log_message('시스템이 일시정지되었습니다.')
                logger.info("시스템 일시정지")
                
        except Exception as e:
            self.log_message(f'시스템 일시정지 중 오류 발생: {str(e)}')
            logger.error(f"시스템 일시정지 중 오류 발생: {str(e)}")
            
    def save_settings(self):
        """설정 저장"""
        try:
            # 설정 데이터 수집
            settings = {
                'algorithm': self.algorithm_combo.currentText(),
                'iterations': self.iterations_spin.value(),
                'time_limit': self.time_limit_spin.value(),
                'time_constraint': self.time_constraint_check.isChecked(),
                'capacity_constraint': self.capacity_constraint_check.isChecked(),
                'priority': self.priority_check.isChecked()
            }
            
            # 설정 저장 로직 구현
            self.log_message('설정이 저장되었습니다.')
            logger.info(f"설정 저장 완료: {settings}")
            
        except Exception as e:
            self.log_message(f'설정 저장 중 오류 발생: {str(e)}')
            logger.error(f"설정 저장 중 오류 발생: {str(e)}")
            
    def save_log(self):
        """로그 저장"""
        try:
            # 파일 저장 대화상자 표시
            file_name, _ = QFileDialog.getSaveFileName(
                self,
                "로그 저장",
                "",
                "텍스트 파일 (*.txt);;모든 파일 (*.*)"
            )
            
            if file_name:
                # 로그 내용 저장
                with open(file_name, 'w', encoding='utf-8') as f:
                    f.write(self.log_text.toPlainText())
                    
                self.log_message(f'로그가 저장되었습니다: {file_name}')
                logger.info(f"로그 저장 완료: {file_name}")
                
        except Exception as e:
            self.log_message(f'로그 저장 중 오류 발생: {str(e)}')
            logger.error(f"로그 저장 중 오류 발생: {str(e)}")
            
    def clear_log(self):
        """로그 지우기"""
        self.log_text.clear()
        self.log_message('로그가 지워졌습니다.')
        logger.info("로그 초기화")
        
    def log_message(self, message: str):
        """
        로그 메시지 추가
        
        Args:
            message (str): 로그 메시지
        """
        timestamp = QDateTime.currentDateTime().toString('yyyy-MM-dd hh:mm:ss')
        self.log_text.append(f'[{timestamp}] {message}')
        
    def update_status(self):
        """상태 업데이트"""
        # 상태 업데이트 로직 구현
        pass
        
    def closeEvent(self, event):
        """
        프로그램 종료 시 처리
        
        Args:
            event: 종료 이벤트
        """
        reply = QMessageBox.question(
            self,
            '종료 확인',
            '프로그램을 종료하시겠습니까?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            event.accept()
            logger.info("프로그램 종료")
        else:
            event.ignore()
            
def main():
    """메인 함수"""
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
            