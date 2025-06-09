# 필요한 라이브러리 임포트
import customtkinter as ctk  # GUI 라이브러리
import pygame  # 사운드 처리를 위한 라이브러리
from gui import AppGUI  # GUI 클래스
from data_loader import DataLoader  # 데이터 로더 클래스
from scheduler import Scheduler  # 스케줄러 클래스
from route_optimizer import RouteOptimizer  # 경로 최적화 클래스

def main():
    # 각 컴포넌트 초기화
    loader = DataLoader()  # 데이터 로더 생성
    scheduler = Scheduler(loader)  # 스케줄러 생성
    route_opt = RouteOptimizer(loader)  # 경로 최적화기 생성
    
    # GUI 생성 및 실행
    app = AppGUI(scheduler, route_opt, loader)  # GUI 애플리케이션 생성
    app.iconbitmap("data/icon.png")  # 애플리케이션 아이콘 설정
    pygame.mixer.init()  # 사운드 시스템 초기화
    app.mainloop()  # GUI 메인 루프 실행

# 프로그램의 진입점
if __name__ == "__main__":
    main()

