# 필요한 라이브러리 임포트
import pandas as pd
from models import Subject, Teacher, Location, TimeSlot
from typing import List
import os
import json
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

# 로거 설정
logger = logging.getLogger(__name__)

class DataLoader:
    """데이터 로딩을 담당하는 클래스"""
    def __init__(self, data_dir='data'):
        """데이터 로더 초기화
        Args:
            data_dir (str): 데이터 파일이 저장된 디렉토리 경로
        """
        self.data_dir = data_dir
        self.subjects = self.load_subjects()
        self.teachers = self.load_teachers()
        self.locations = self.load_locations()
        self.time_slots = self.load_time_slots()
        self.teacher_assignments = self.load_teacher_assignments()

    def load_subjects(self) -> List[Subject]:
        """과목 정보 로드
        Returns:
            List[Subject]: 과목 객체 리스트
        """
        df = pd.read_csv(f'{self.data_dir}/subjects.csv')
        return [Subject(row['subject'], row['teachers'].split(','), row['required'] == 'true') for _, row in df.iterrows()]

    def load_teachers(self) -> List[Teacher]:
        """교사 정보 로드
        Returns:
            List[Teacher]: 교사 객체 리스트
        """
        # 모든 과목의 teacher를 합쳐서 유니크하게 만듦
        teachers = set()
        for subj in self.load_subjects():
            teachers.update(subj.teachers)
        return [Teacher(name) for name in teachers if name]

    def load_locations(self) -> List[Location]:
        """위치 정보 로드
        Returns:
            List[Location]: 위치 객체 리스트
        """
        df = pd.read_csv(f'{self.data_dir}/locations.csv')
        return [Location(row['building'], int(row['floor']), row['room_number'], float(row['x_coord']), float(row['y_coord'])) for _, row in df.iterrows()]

    def load_time_slots(self) -> List[TimeSlot]:
        """시간 정보 로드
        Returns:
            List[TimeSlot]: 시간 객체 리스트
        """
        df = pd.read_csv(f'{self.data_dir}/time_slots.csv')
        return [TimeSlot(row['day'], int(row['period']), row['start_time'], row['end_time']) for _, row in df.iterrows()]

    def load_teacher_assignments(self):
        """교사 배정 정보 로드
        Returns:
            list: 교사 배정 정보 딕셔너리 리스트
        """
        df = pd.read_csv(f'{self.data_dir}/teacher_assignments.csv')
        return df.to_dict('records')

class DataManager:
    """
    데이터 관리 및 처리를 담당하는 클래스
    
    이 클래스는 다양한 형식의 데이터를 로드하고,
    전처리하며, 저장하는 기능을 제공합니다.
    """
    
    def __init__(self, data_dir: str = 'data'):
        """
        DataManager 초기화
        
        Args:
            data_dir (str): 데이터 파일이 저장된 디렉토리 경로
        """
        self.data_dir = data_dir
        self.cache = {}  # 데이터 캐시
        self.last_modified = {}  # 파일별 마지막 수정 시간
        
        # 데이터 디렉토리가 없으면 생성
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
            logger.info(f"데이터 디렉토리 생성됨: {data_dir}")
            
    def load_data(self,
                 file_name: str,
                 file_type: str = None) -> Optional[pd.DataFrame]:
        """
        데이터 파일 로드
        
        Args:
            file_name (str): 파일명
            file_type (str, optional): 파일 형식 (자동 감지되지 않는 경우)
            
        Returns:
            Optional[pd.DataFrame]: 로드된 데이터
        """
        try:
            file_path = os.path.join(self.data_dir, file_name)
            
            # 파일이 존재하는지 확인
            if not os.path.exists(file_path):
                logger.error(f"파일을 찾을 수 없음: {file_path}")
                return None
                
            # 파일 수정 시간 확인
            current_mtime = os.path.getmtime(file_path)
            if file_path in self.last_modified and current_mtime == self.last_modified[file_path]:
                logger.info("캐시된 데이터 사용")
                return self.cache.get(file_path)
                
            # 파일 형식 결정
            if file_type is None:
                file_type = self._detect_file_type(file_name)
                
            # 파일 형식에 따라 데이터 로드
            if file_type == 'csv':
                data = pd.read_csv(file_path)
            elif file_type == 'json':
                data = pd.read_json(file_path)
            elif file_type == 'excel':
                data = pd.read_excel(file_path)
            else:
                logger.error(f"지원하지 않는 파일 형식: {file_type}")
                return None
                
            # 데이터 전처리
            data = self._preprocess_data(data)
            
            # 캐시 업데이트
            self.cache[file_path] = data
            self.last_modified[file_path] = current_mtime
            
            logger.info(f"데이터 로드 완료: {file_path}")
            return data
            
        except Exception as e:
            logger.error(f"데이터 로드 중 오류 발생: {str(e)}")
            return None
            
    def save_data(self,
                 data: pd.DataFrame,
                 file_name: str,
                 file_type: str = None) -> bool:
        """
        데이터를 파일로 저장
        
        Args:
            data (pd.DataFrame): 저장할 데이터
            file_name (str): 저장할 파일명
            file_type (str, optional): 파일 형식
            
        Returns:
            bool: 저장 성공 여부
        """
        try:
            file_path = os.path.join(self.data_dir, file_name)
            
            # 파일 형식 결정
            if file_type is None:
                file_type = self._detect_file_type(file_name)
                
            # 파일 형식에 따라 데이터 저장
            if file_type == 'csv':
                data.to_csv(file_path, index=False)
            elif file_type == 'json':
                data.to_json(file_path, orient='records')
            elif file_type == 'excel':
                data.to_excel(file_path, index=False)
            else:
                logger.error(f"지원하지 않는 파일 형식: {file_type}")
                return False
                
            # 캐시 업데이트
            self.cache[file_path] = data
            self.last_modified[file_path] = os.path.getmtime(file_path)
            
            logger.info(f"데이터 저장 완료: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"데이터 저장 중 오류 발생: {str(e)}")
            return False
            
    def _detect_file_type(self, file_name: str) -> str:
        """
        파일 형식 감지
        
        Args:
            file_name (str): 파일명
            
        Returns:
            str: 감지된 파일 형식
        """
        extension = os.path.splitext(file_name)[1].lower()
        
        if extension == '.csv':
            return 'csv'
        elif extension == '.json':
            return 'json'
        elif extension in ['.xlsx', '.xls']:
            return 'excel'
        else:
            logger.warning(f"알 수 없는 파일 형식: {extension}")
            return None
            
    def _preprocess_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        데이터 전처리
        
        Args:
            data (pd.DataFrame): 전처리할 데이터
            
        Returns:
            pd.DataFrame: 전처리된 데이터
        """
        try:
            # 결측치 처리
            data = self._handle_missing_values(data)
            
            # 데이터 타입 변환
            data = self._convert_data_types(data)
            
            # 중복 데이터 처리
            data = self._handle_duplicates(data)
            
            # 이상치 처리
            data = self._handle_outliers(data)
            
            return data
            
        except Exception as e:
            logger.error(f"데이터 전처리 중 오류 발생: {str(e)}")
            return data
            
    def _handle_missing_values(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        결측치 처리
        
        Args:
            data (pd.DataFrame): 처리할 데이터
            
        Returns:
            pd.DataFrame: 결측치가 처리된 데이터
        """
        # 숫자형 컬럼의 결측치를 평균값으로 대체
        numeric_columns = data.select_dtypes(include=[np.number]).columns
        for col in numeric_columns:
            data[col] = data[col].fillna(data[col].mean())
            
        # 범주형 컬럼의 결측치를 최빈값으로 대체
        categorical_columns = data.select_dtypes(include=['object']).columns
        for col in categorical_columns:
            data[col] = data[col].fillna(data[col].mode()[0])
            
        return data
        
    def _convert_data_types(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        데이터 타입 변환
        
        Args:
            data (pd.DataFrame): 변환할 데이터
            
        Returns:
            pd.DataFrame: 데이터 타입이 변환된 데이터
        """
        # 날짜/시간 컬럼 변환
        date_columns = [col for col in data.columns if 'date' in col.lower() or 'time' in col.lower()]
        for col in date_columns:
            try:
                data[col] = pd.to_datetime(data[col])
            except:
                pass
                
        # 숫자형 컬럼 변환
        numeric_columns = [col for col in data.columns if 'id' in col.lower() or 'count' in col.lower()]
        for col in numeric_columns:
            try:
                data[col] = pd.to_numeric(data[col])
            except:
                pass
                
        return data
        
    def _handle_duplicates(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        중복 데이터 처리
        
        Args:
            data (pd.DataFrame): 처리할 데이터
            
        Returns:
            pd.DataFrame: 중복이 제거된 데이터
        """
        # ID 컬럼이 있는 경우 해당 컬럼 기준으로 중복 제거
        id_columns = [col for col in data.columns if 'id' in col.lower()]
        if id_columns:
            data = data.drop_duplicates(subset=id_columns)
        else:
            # ID 컬럼이 없는 경우 모든 컬럼 기준으로 중복 제거
            data = data.drop_duplicates()
            
        return data
        
    def _handle_outliers(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        이상치 처리
        
        Args:
            data (pd.DataFrame): 처리할 데이터
            
        Returns:
            pd.DataFrame: 이상치가 처리된 데이터
        """
        # 숫자형 컬럼에 대해서만 이상치 처리
        numeric_columns = data.select_dtypes(include=[np.number]).columns
        
        for col in numeric_columns:
            # IQR 방식으로 이상치 탐지
            Q1 = data[col].quantile(0.25)
            Q3 = data[col].quantile(0.75)
            IQR = Q3 - Q1
            
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            # 이상치를 경계값으로 대체
            data[col] = data[col].clip(lower=lower_bound, upper=upper_bound)
            
        return data
        
    def clear_cache(self):
        """데이터 캐시 초기화"""
        self.cache.clear()
        self.last_modified.clear()
        logger.info("데이터 캐시가 초기화되었습니다.")
        
    def get_data_info(self, file_name: str) -> Dict[str, Any]:
        """
        데이터 파일 정보 조회
        
        Args:
            file_name (str): 파일명
            
        Returns:
            Dict[str, Any]: 파일 정보
        """
        try:
            file_path = os.path.join(self.data_dir, file_name)
            
            if not os.path.exists(file_path):
                logger.error(f"파일을 찾을 수 없음: {file_path}")
                return {}
                
            # 파일 정보 수집
            file_info = {
                'file_name': file_name,
                'file_size': os.path.getsize(file_path),
                'last_modified': datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat(),
                'file_type': self._detect_file_type(file_name)
            }
            
            # 데이터가 캐시에 있는 경우 추가 정보 수집
            if file_path in self.cache:
                data = self.cache[file_path]
                file_info.update({
                    'row_count': len(data),
                    'column_count': len(data.columns),
                    'column_names': list(data.columns),
                    'data_types': {col: str(dtype) for col, dtype in data.dtypes.items()}
                })
                
            return file_info
            
        except Exception as e:
            logger.error(f"파일 정보 조회 중 오류 발생: {str(e)}")
            return {} 