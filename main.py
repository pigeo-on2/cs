# 필요한 라이브러리 임포트
import customtkinter as ctk  # GUI 라이브러리
import pygame  # 사운드 처리를 위한 라이브러리
from gui import AppGUI  # GUI 클래스
from data_loader import DataLoader  # 데이터 로더 클래스
from scheduler import Scheduler  # 스케줄러 클래스
from route_optimizer import RouteOptimizer  # 경로 최적화 클래스
import os
import sys
import json
import time
import logging
import numpy as np
import pandas as pd
from datetime import datetime
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QIcon

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

# 필요한 모듈들을 임포트
from data_loader import DataLoader
from models import RouteOptimizer
from scheduler import DeliveryScheduler
from gui import MainWindow
from data_manager_gui import DataManagerWindow
from visualizer import RouteVisualizer
from graph_util import GraphUtil
from loader import DataManager

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('delivery_optimization.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class DeliveryOptimizationSystem:
    """
    배달 최적화 시스템의 메인 클래스
    전체 시스템의 초기화, 실행, 종료를 관리
    """
    
    def __init__(self):
        """시스템 초기화 및 필요한 컴포넌트들을 생성"""
        # GUI 애플리케이션 초기화
        self.app = QApplication(sys.argv)
        self.app.setStyle('Fusion')  # 모던한 Fusion 스타일 적용
        
        # 시스템 상태 변수들 초기화
        self.is_running = False  # 시스템 실행 상태
        self.is_paused = False   # 일시 정지 상태
        self.current_cycle = 0   # 현재 최적화 사이클
        self.last_optimization_time = None  # 마지막 최적화 시간
        
        # 데이터 관리자 초기화
        self.data_manager = DataManager()
        
        # GUI 컴포넌트 초기화
        self.main_window = MainWindow(self)  # 메인 윈도우
        self.data_manager_window = DataManagerWindow(self.data_manager)  # 데이터 관리 윈도우
        
        # 데이터 로더 초기화
        self.data_loader = DataLoader()
        
        # 최적화 관련 컴포넌트들 초기화
        self.route_optimizer = RouteOptimizer()  # 경로 최적화기
        self.scheduler = DeliveryScheduler()     # 배달 스케줄러
        self.visualizer = RouteVisualizer()      # 시각화 도구
        
        # 타이머 설정
        self.optimization_timer = QTimer()  # 최적화 주기 타이머
        self.optimization_timer.timeout.connect(self.run_optimization_cycle)
        
        # 상태 모니터링 타이머
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_system_status)
        self.status_timer.start(1000)  # 1초마다 상태 업데이트
        
        # 시스템 설정 로드
        self.load_system_settings()
        
        # GUI 이벤트 핸들러 연결
        self.setup_event_handlers()
        
        logger.info("시스템이 성공적으로 초기화되었습니다.")

    def load_system_settings(self):
        """시스템 설정을 로드하고 적용"""
        try:
            # 설정 파일 경로
            settings_path = os.path.join(project_root, 'config', 'system_settings.json')
            
            # 설정 파일이 존재하는 경우 로드
            if os.path.exists(settings_path):
                with open(settings_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    
                # 최적화 주기 설정
                self.optimization_interval = settings.get('optimization_interval', 300)  # 기본값 5분
                
                # 기타 설정들 적용
                self.max_vehicles = settings.get('max_vehicles', 10)
                self.max_capacity = settings.get('max_capacity', 1000)
                self.time_window = settings.get('time_window', 3600)
                
                logger.info("시스템 설정이 성공적으로 로드되었습니다.")
            else:
                # 기본 설정값 사용
                self.optimization_interval = 300
                self.max_vehicles = 10
                self.max_capacity = 1000
                self.time_window = 3600
                logger.warning("설정 파일을 찾을 수 없어 기본값을 사용합니다.")
                
        except Exception as e:
            logger.error(f"설정 로드 중 오류 발생: {str(e)}")
            # 오류 발생 시 기본값 사용
            self.optimization_interval = 300
            self.max_vehicles = 10
            self.max_capacity = 1000
            self.time_window = 3600

    def setup_event_handlers(self):
        """GUI 이벤트 핸들러 설정"""
        # 메인 윈도우 이벤트 연결
        self.main_window.start_button.clicked.connect(self.start_system)
        self.main_window.stop_button.clicked.connect(self.stop_system)
        self.main_window.pause_button.clicked.connect(self.toggle_pause)
        self.main_window.settings_button.clicked.connect(self.show_settings)
        self.main_window.data_manager_button.clicked.connect(self.show_data_manager)
        
        # 데이터 관리자 윈도우 이벤트 연결
        self.data_manager_window.data_updated.connect(self.on_data_updated)

    def start_system(self):
        """시스템 시작"""
        if not self.is_running:
            self.is_running = True
            self.is_paused = False
            self.optimization_timer.start(self.optimization_interval * 1000)
            logger.info("시스템이 시작되었습니다.")
            self.main_window.update_status("시스템 실행 중")

    def stop_system(self):
        """시스템 중지"""
        if self.is_running:
            self.is_running = False
            self.is_paused = False
            self.optimization_timer.stop()
            logger.info("시스템이 중지되었습니다.")
            self.main_window.update_status("시스템 중지됨")

    def toggle_pause(self):
        """시스템 일시 정지/재개"""
        if self.is_running:
            self.is_paused = not self.is_paused
            if self.is_paused:
                self.optimization_timer.stop()
                logger.info("시스템이 일시 정지되었습니다.")
                self.main_window.update_status("일시 정지됨")
            else:
                self.optimization_timer.start(self.optimization_interval * 1000)
                logger.info("시스템이 재개되었습니다.")
                self.main_window.update_status("시스템 실행 중")

    def show_settings(self):
        """설정 창 표시"""
        # TODO: 설정 창 구현
        logger.info("설정 창을 표시합니다.")

    def show_data_manager(self):
        """데이터 관리자 창 표시"""
        self.data_manager_window.show()
        logger.info("데이터 관리자 창을 표시합니다.")

    def on_data_updated(self):
        """데이터 업데이트 시 호출되는 콜백"""
        logger.info("데이터가 업데이트되었습니다.")
        self.main_window.update_status("데이터 업데이트됨")

    def run_optimization_cycle(self):
        """최적화 사이클 실행"""
        if not self.is_running or self.is_paused:
            return

        try:
            # 현재 시간 기록
            current_time = datetime.now()
            self.last_optimization_time = current_time
            
            # 데이터 로드
            delivery_data = self.data_loader.load_delivery_data()
            vehicle_data = self.data_loader.load_vehicle_data()
            
            # 데이터 유효성 검사
            if not self.validate_data(delivery_data, vehicle_data):
                logger.error("데이터 유효성 검사 실패")
                return
            
            # 경로 최적화 실행
            optimized_routes = self.route_optimizer.optimize(
                delivery_data,
                vehicle_data,
                max_vehicles=self.max_vehicles,
                max_capacity=self.max_capacity,
                time_window=self.time_window
            )
            
            # 스케줄 생성
            schedule = self.scheduler.create_schedule(optimized_routes)
            
            # 결과 시각화
            self.visualizer.visualize_routes(optimized_routes)
            
            # 결과 저장
            self.save_optimization_results(optimized_routes, schedule)
            
            # GUI 업데이트
            self.main_window.update_optimization_results(optimized_routes, schedule)
            
            # 사이클 카운터 증가
            self.current_cycle += 1
            
            logger.info(f"최적화 사이클 {self.current_cycle} 완료")
            
        except Exception as e:
            logger.error(f"최적화 사이클 실행 중 오류 발생: {str(e)}")
            self.main_window.update_status("오류 발생")

    def validate_data(self, delivery_data, vehicle_data):
        """데이터 유효성 검사"""
        try:
            # 배달 데이터 검사
            if delivery_data is None or len(delivery_data) == 0:
                logger.error("배달 데이터가 비어있습니다.")
                return False
                
            # 차량 데이터 검사
            if vehicle_data is None or len(vehicle_data) == 0:
                logger.error("차량 데이터가 비어있습니다.")
                return False
                
            # 필수 필드 검사
            required_delivery_fields = ['id', 'pickup_location', 'delivery_location', 'time_window']
            required_vehicle_fields = ['id', 'capacity', 'current_location']
            
            for field in required_delivery_fields:
                if field not in delivery_data.columns:
                    logger.error(f"배달 데이터에 필수 필드 '{field}'가 없습니다.")
                    return False
                    
            for field in required_vehicle_fields:
                if field not in vehicle_data.columns:
                    logger.error(f"차량 데이터에 필수 필드 '{field}'가 없습니다.")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"데이터 유효성 검사 중 오류 발생: {str(e)}")
            return False

    def save_optimization_results(self, routes, schedule):
        """최적화 결과 저장"""
        try:
            # 결과 저장 디렉토리 생성
            results_dir = os.path.join(project_root, 'results')
            os.makedirs(results_dir, exist_ok=True)
            
            # 현재 시간을 파일명에 포함
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # 경로 데이터 저장
            routes_file = os.path.join(results_dir, f'routes_{timestamp}.json')
            with open(routes_file, 'w', encoding='utf-8') as f:
                json.dump(routes, f, ensure_ascii=False, indent=2)
            
            # 스케줄 데이터 저장
            schedule_file = os.path.join(results_dir, f'schedule_{timestamp}.json')
            with open(schedule_file, 'w', encoding='utf-8') as f:
                json.dump(schedule, f, ensure_ascii=False, indent=2)
            
            logger.info(f"최적화 결과가 저장되었습니다: {routes_file}, {schedule_file}")
            
        except Exception as e:
            logger.error(f"결과 저장 중 오류 발생: {str(e)}")

    def update_system_status(self):
        """시스템 상태 업데이트"""
        if self.is_running:
            if self.is_paused:
                status = "일시 정지됨"
            else:
                status = "실행 중"
                
            # 마지막 최적화 시간이 있는 경우 경과 시간 계산
            if self.last_optimization_time:
                elapsed = datetime.now() - self.last_optimization_time
                status += f" (마지막 최적화: {elapsed.seconds}초 전)"
                
            self.main_window.update_status(status)

    def run(self):
        """시스템 실행"""
        try:
            # 메인 윈도우 표시
            self.main_window.show()
            
            # 이벤트 루프 시작
            return self.app.exec_()
            
        except Exception as e:
            logger.error(f"시스템 실행 중 오류 발생: {str(e)}")
            return 1

def main():
    """메인 함수"""
    try:
        # 시스템 인스턴스 생성
        system = DeliveryOptimizationSystem()
        
        # 시스템 실행
        return system.run()
        
    except Exception as e:
        logger.error(f"프로그램 실행 중 오류 발생: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())

