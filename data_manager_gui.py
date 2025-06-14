# 필요한 라이브러리 임포트
import customtkinter as ctk
import pandas as pd
from tkinter import messagebox
import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                           QHBoxLayout, QPushButton, QLabel, QFileDialog,
                           QTableWidget, QTableWidgetItem, QMessageBox)
from PyQt5.QtCore import Qt
import logging

# 로거 설정
logger = logging.getLogger(__name__)

class DataManagerGUI(QMainWindow):
    """
    데이터 관리 GUI 클래스
    
    이 클래스는 데이터 관리 기능을 위한 그래픽 사용자 인터페이스를 제공합니다.
    데이터 로드, 저장, 편집 등의 기능을 포함합니다.
    """
    
    def __init__(self):
        """DataManagerGUI 초기화"""
        super().__init__()
        self.init_ui()
        self.data = None
        self.current_file = None
        
    def init_ui(self):
        """사용자 인터페이스 초기화"""
        # 메인 윈도우 설정
        self.setWindowTitle('데이터 관리 시스템')
        self.setGeometry(100, 100, 800, 600)
        
        # 중앙 위젯 생성
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 메인 레이아웃 설정
        layout = QVBoxLayout(central_widget)
        
        # 버튼 레이아웃 생성
        button_layout = QHBoxLayout()
        
        # 데이터 로드 버튼
        self.load_button = QPushButton('데이터 로드')
        self.load_button.clicked.connect(self.load_data)
        button_layout.addWidget(self.load_button)
        
        # 데이터 저장 버튼
        self.save_button = QPushButton('데이터 저장')
        self.save_button.clicked.connect(self.save_data)
        button_layout.addWidget(self.save_button)
        
        # 데이터 편집 버튼
        self.edit_button = QPushButton('데이터 편집')
        self.edit_button.clicked.connect(self.edit_data)
        button_layout.addWidget(self.edit_button)
        
        # 버튼 레이아웃을 메인 레이아웃에 추가
        layout.addLayout(button_layout)
        
        # 데이터 테이블 생성
        self.table = QTableWidget()
        layout.addWidget(self.table)
        
        # 상태 표시줄 생성
        self.statusBar().showMessage('준비')
        
    def load_data(self):
        """데이터 파일 로드"""
        try:
            # 파일 선택 대화상자 표시
            file_name, _ = QFileDialog.getOpenFileName(
                self,
                "데이터 파일 선택",
                "",
                "CSV 파일 (*.csv);;Excel 파일 (*.xlsx *.xls);;모든 파일 (*.*)"
            )
            
            if file_name:
                # 파일 확장자에 따라 데이터 로드
                if file_name.endswith('.csv'):
                    self.data = pd.read_csv(file_name)
                elif file_name.endswith(('.xlsx', '.xls')):
                    self.data = pd.read_excel(file_name)
                else:
                    QMessageBox.warning(self, '경고', '지원하지 않는 파일 형식입니다.')
                    return
                    
                # 테이블 업데이트
                self.update_table()
                self.current_file = file_name
                self.statusBar().showMessage(f'파일 로드됨: {file_name}')
                logger.info(f"데이터 파일 로드 완료: {file_name}")
                
        except Exception as e:
            QMessageBox.critical(self, '오류', f'데이터 로드 중 오류 발생: {str(e)}')
            logger.error(f"데이터 로드 중 오류 발생: {str(e)}")
            
    def save_data(self):
        """데이터 파일 저장"""
        try:
            if self.data is None:
                QMessageBox.warning(self, '경고', '저장할 데이터가 없습니다.')
                return
                
            # 파일 저장 대화상자 표시
            file_name, _ = QFileDialog.getSaveFileName(
                self,
                "데이터 저장",
                "",
                "CSV 파일 (*.csv);;Excel 파일 (*.xlsx);;모든 파일 (*.*)"
            )
            
            if file_name:
                # 파일 확장자에 따라 데이터 저장
                if file_name.endswith('.csv'):
                    self.data.to_csv(file_name, index=False)
                elif file_name.endswith('.xlsx'):
                    self.data.to_excel(file_name, index=False)
                else:
                    QMessageBox.warning(self, '경고', '지원하지 않는 파일 형식입니다.')
                    return
                    
                self.current_file = file_name
                self.statusBar().showMessage(f'파일 저장됨: {file_name}')
                logger.info(f"데이터 파일 저장 완료: {file_name}")
                
        except Exception as e:
            QMessageBox.critical(self, '오류', f'데이터 저장 중 오류 발생: {str(e)}')
            logger.error(f"데이터 저장 중 오류 발생: {str(e)}")
            
    def edit_data(self):
        """데이터 편집"""
        try:
            if self.data is None:
                QMessageBox.warning(self, '경고', '편집할 데이터가 없습니다.')
                return
                
            # 편집 모드 활성화
            self.table.setEditTriggers(QTableWidget.DoubleClicked)
            self.statusBar().showMessage('편집 모드 활성화')
            logger.info("데이터 편집 모드 활성화")
            
        except Exception as e:
            QMessageBox.critical(self, '오류', f'데이터 편집 중 오류 발생: {str(e)}')
            logger.error(f"데이터 편집 중 오류 발생: {str(e)}")
            
    def update_table(self):
        """테이블 위젯 업데이트"""
        try:
            if self.data is None:
                return
                
            # 테이블 크기 설정
            self.table.setRowCount(len(self.data))
            self.table.setColumnCount(len(self.data.columns))
            
            # 컬럼 헤더 설정
            self.table.setHorizontalHeaderLabels(self.data.columns)
            
            # 데이터 채우기
            for i in range(len(self.data)):
                for j in range(len(self.data.columns)):
                    value = str(self.data.iloc[i, j])
                    item = QTableWidgetItem(value)
                    self.table.setItem(i, j, item)
                    
            # 컬럼 크기 자동 조정
            self.table.resizeColumnsToContents()
            logger.info("테이블 업데이트 완료")
            
        except Exception as e:
            QMessageBox.critical(self, '오류', f'테이블 업데이트 중 오류 발생: {str(e)}')
            logger.error(f"테이블 업데이트 중 오류 발생: {str(e)}")
            
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
    window = DataManagerGUI()
    window.show()
    sys.exit(app.exec_())

class DataManagerGUI:
    """데이터 관리 GUI 클래스"""
    def __init__(self, parent, loader):
        """데이터 관리 GUI 초기화
        Args:
            parent: 부모 윈도우
            loader: 데이터 로더 객체
        """
        self.parent = parent
        self.loader = loader
        
        # 탭뷰 생성
        self.tabview = ctk.CTkTabview(parent)
        self.tabview.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        
        # 탭 생성
        self.tab_locations = self.tabview.add("위치 관리")
        self.tab_subjects = self.tabview.add("과목 관리")
        self.tab_teachers = self.tabview.add("교사 관리")
        
        self.create_locations_tab()
        self.create_subjects_tab()
        self.create_school_data_tab()

    def create_locations_tab(self):
        """위치 관리 탭 생성"""
        frame = ctk.CTkFrame(self.tab_locations)
        frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        frame.grid_columnconfigure(0, weight=1)
        
        # 제목
        title = ctk.CTkLabel(frame, text="위치 관리", font=ctk.CTkFont(size=16, weight="bold"))
        title.grid(row=0, column=0, padx=10, pady=(10, 20))
        
        # 입력 프레임
        input_frame = ctk.CTkFrame(frame)
        input_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        input_frame.grid_columnconfigure((0,1,2), weight=1)
        
        # 입력 필드
        self.loc_building = ctk.CTkEntry(input_frame, placeholder_text="건물명")
        self.loc_building.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        
        self.loc_floor = ctk.CTkEntry(input_frame, placeholder_text="층")
        self.loc_floor.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        self.loc_room = ctk.CTkEntry(input_frame, placeholder_text="호수")
        self.loc_room.grid(row=0, column=2, padx=5, pady=5, sticky="ew")
        
        self.loc_x = ctk.CTkEntry(input_frame, placeholder_text="X 좌표")
        self.loc_x.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        
        self.loc_y = ctk.CTkEntry(input_frame, placeholder_text="Y 좌표")
        self.loc_y.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        
        # 추가 버튼
        add_btn = ctk.CTkButton(input_frame, text="위치 추가", command=self.add_location)
        add_btn.grid(row=1, column=2, padx=5, pady=5, sticky="ew")
        
        # 위치 목록
        list_frame = ctk.CTkFrame(frame)
        list_frame.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")
        list_frame.grid_columnconfigure(0, weight=1)
        list_frame.grid_rowconfigure(0, weight=1)
        
        self.loc_list = ctk.CTkTextbox(list_frame, width=400, height=200)
        self.loc_list.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.update_location_list()

    def create_subjects_tab(self):
        """과목 관리 탭 생성"""
        frame = ctk.CTkFrame(self.tab_subjects)
        frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        frame.grid_columnconfigure(0, weight=1)
        
        # 제목
        title = ctk.CTkLabel(frame, text="과목 관리", font=ctk.CTkFont(size=16, weight="bold"))
        title.grid(row=0, column=0, padx=10, pady=(10, 20))
        
        # 입력 프레임
        input_frame = ctk.CTkFrame(frame)
        input_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        input_frame.grid_columnconfigure((0,1,2), weight=1)
        
        # 입력 필드
        self.subj_name = ctk.CTkEntry(input_frame, placeholder_text="과목명")
        self.subj_name.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        
        self.subj_teacher = ctk.CTkEntry(input_frame, placeholder_text="담당 교사")
        self.subj_teacher.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        self.subj_classes = ctk.CTkEntry(input_frame, placeholder_text="담당 반 (쉼표로 구분)")
        self.subj_classes.grid(row=0, column=2, padx=5, pady=5, sticky="ew")
        
        # 추가 버튼
        add_btn = ctk.CTkButton(input_frame, text="과목 추가", command=self.add_subject)
        add_btn.grid(row=1, column=0, columnspan=3, padx=5, pady=5, sticky="ew")
        
        # 과목 목록
        list_frame = ctk.CTkFrame(frame)
        list_frame.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")
        list_frame.grid_columnconfigure(0, weight=1)
        list_frame.grid_rowconfigure(0, weight=1)
        
        self.subj_list = ctk.CTkTextbox(list_frame, width=400, height=200)
        self.subj_list.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.update_subject_list()

    def create_school_data_tab(self):
        """학교 데이터 관리 탭 생성"""
        frame = ctk.CTkFrame(self.tab_teachers)
        frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        frame.grid_columnconfigure(0, weight=1)
        
        # 제목
        title = ctk.CTkLabel(frame, text="교사/과목/반/교실 관리", font=ctk.CTkFont(size=16, weight="bold"))
        title.grid(row=0, column=0, padx=10, pady=(10, 20))
        
        # 입력 프레임
        input_frame = ctk.CTkFrame(frame)
        input_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        input_frame.grid_columnconfigure((0,1,2,3), weight=1)
        
        # 입력 필드
        self.sd_teacher = ctk.CTkEntry(input_frame, placeholder_text="선생님")
        self.sd_teacher.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        self.sd_subject = ctk.CTkEntry(input_frame, placeholder_text="과목")
        self.sd_subject.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.sd_room = ctk.CTkEntry(input_frame, placeholder_text="담당 교실")
        self.sd_room.grid(row=0, column=2, padx=5, pady=5, sticky="ew")
        self.sd_classes = ctk.CTkEntry(input_frame, placeholder_text="담당 반 (쉼표로 구분)")
        self.sd_classes.grid(row=0, column=3, padx=5, pady=5, sticky="ew")
        
        # 추가 버튼
        add_btn = ctk.CTkButton(input_frame, text="추가", command=self.add_school_data)
        add_btn.grid(row=1, column=0, columnspan=4, padx=5, pady=5, sticky="ew")
        
        # 목록
        list_frame = ctk.CTkFrame(frame)
        list_frame.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")
        list_frame.grid_columnconfigure(0, weight=1)
        list_frame.grid_rowconfigure(0, weight=1)
        self.school_data_list = ctk.CTkTextbox(list_frame, width=600, height=200)
        self.school_data_list.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.update_school_data_list()

    def add_location(self):
        """위치 추가"""
        try:
            building = self.loc_building.get()
            floor = int(self.loc_floor.get())
            room = self.loc_room.get()
            x = float(self.loc_x.get())
            y = float(self.loc_y.get())
            
            # 기존 데이터 로드
            df = pd.read_csv('data/locations.csv')
            
            # 새 위치 추가
            new_row = pd.DataFrame({
                'building': [building],
                'floor': [floor],
                'room_number': [room],
                'x_coord': [x],
                'y_coord': [y]
            })
            df = pd.concat([df, new_row], ignore_index=True)
            
            # CSV 파일에 저장
            df.to_csv('data/locations.csv', index=False)
            
            # UI 업데이트
            self.update_location_list()
            self.clear_location_inputs()
            
            # 부모에게 데이터 재로드 요청
            if hasattr(self.parent, 'route_opt'):
                self.parent.route_opt.locations = self.loader.load_csv('locations').to_dict('records')
                self.parent.route_opt.graph = self.parent.route_opt.build_graph(self.parent.route_opt.locations)
            
            messagebox.showinfo("성공", "위치가 추가되었습니다.")
        except Exception as e:
            messagebox.showerror("오류", f"위치 추가 중 오류가 발생했습니다: {str(e)}")

    def add_subject(self):
        """과목 추가"""
        try:
            subject = self.subj_name.get()
            teacher = self.subj_teacher.get()
            classes = self.subj_classes.get()
            df = pd.read_csv('data/school_data.csv')
            new_row = pd.DataFrame({'과목': [subject], '선생님': [teacher], '담당 반': [classes], '담당 교실': ['']})
            df = pd.concat([df, new_row], ignore_index=True)
            df.to_csv('data/school_data.csv', index=False)
            self.update_subject_list()
            self.clear_subject_inputs()
            messagebox.showinfo("성공", "과목이 추가되었습니다.")
        except Exception as e:
            messagebox.showerror("오류", f"과목 추가 중 오류가 발생했습니다: {str(e)}")

    def add_school_data(self):
        """학교 데이터 추가"""
        try:
            teacher = self.sd_teacher.get()
            subject = self.sd_subject.get()
            room = self.sd_room.get()
            classes = self.sd_classes.get()
            df = pd.read_csv('data/school_data.csv')
            new_row = pd.DataFrame({'선생님': [teacher], '과목': [subject], '담당 교실': [room], '담당 반': [classes]})
            df = pd.concat([df, new_row], ignore_index=True)
            df.to_csv('data/school_data.csv', index=False)
            self.update_school_data_list()
            self.clear_school_data_inputs()
            messagebox.showinfo("성공", "데이터가 추가되었습니다.")
        except Exception as e:
            messagebox.showerror("오류", f"데이터 추가 중 오류가 발생했습니다: {str(e)}")

    def update_location_list(self):
        """위치 목록 업데이트"""
        try:
            df = pd.read_csv('data/locations.csv')
            self.loc_list.delete("1.0", "end")
            for _, row in df.iterrows():
                self.loc_list.insert("end", f"건물: {row['building']}, 층: {row['floor']}, 호수: {row['room_number']}\n")
        except Exception as e:
            self.loc_list.delete("1.0", "end")
            self.loc_list.insert("end", f"위치 목록을 불러오는 중 오류가 발생했습니다: {str(e)}")

    def update_subject_list(self):
        """과목 목록 업데이트"""
        try:
            df = pd.read_csv('data/school_data.csv')
            self.subj_list.delete("1.0", "end")
            for _, row in df.iterrows():
                self.subj_list.insert("end", f"과목: {row['과목']}, 교사: {row['선생님']}, 담당 반: {row['담당 반']}\n")
        except Exception as e:
            self.subj_list.delete("1.0", "end")
            self.subj_list.insert("end", f"과목 목록을 불러오는 중 오류가 발생했습니다: {str(e)}")

    def update_school_data_list(self):
        """학교 데이터 목록 업데이트"""
        try:
            df = pd.read_csv('data/school_data.csv')
            self.school_data_list.delete("1.0", "end")
            for _, row in df.iterrows():
                self.school_data_list.insert("end", f"{row['선생님']} | {row['과목']} | {row['담당 교실']} | {row['담당 반']}\n")
        except Exception as e:
            self.school_data_list.delete("1.0", "end")
            self.school_data_list.insert("end", f"목록을 불러오는 중 오류가 발생했습니다: {str(e)}")

    def clear_location_inputs(self):
        """위치 입력 필드 초기화"""
        self.loc_building.delete(0, "end")
        self.loc_floor.delete(0, "end")
        self.loc_room.delete(0, "end")
        self.loc_x.delete(0, "end")
        self.loc_y.delete(0, "end")

    def clear_subject_inputs(self):
        """과목 입력 필드 초기화"""
        self.subj_name.delete(0, "end")
        self.subj_teacher.delete(0, "end")
        self.subj_classes.delete(0, "end")

    def clear_school_data_inputs(self):
        """학교 데이터 입력 필드 초기화"""
        self.sd_teacher.delete(0, "end")
        self.sd_subject.delete(0, "end")
        self.sd_room.delete(0, "end")
        self.sd_classes.delete(0, "end") 