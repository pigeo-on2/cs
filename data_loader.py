# 필요한 라이브러리 임포트
import pandas as pd
import json
from models import Teacher, Location
from typing import List
import os
import numpy as np
from datetime import datetime, timedelta
import logging

# 로거 설정
logger = logging.getLogger(__name__)

class DataLoader:
    """학교 데이터를 로드하고 관리하는 클래스"""
    def __init__(self, data_dir='data'):
        """데이터 로더 초기화
        Args:
            data_dir (str): 데이터 파일이 저장된 디렉토리 경로
        """
        self.data_dir = data_dir
        self.school_data = self.load_school_data()
        self.locations = self.load_locations()
        self.cache = {}  # 데이터 캐시
        self.last_modified = {}  # 파일별 마지막 수정 시간
        
        # 데이터 디렉토리가 없으면 생성
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
            logger.info(f"데이터 디렉토리 생성됨: {data_dir}")

    def load_school_data(self):
        """학교 데이터를 CSV 파일에서 로드"""
        df = pd.read_csv(f'{self.data_dir}/school_data.csv')
        return df.to_dict('records')

    def load_teachers(self) -> List[Teacher]:
        """교사 정보를 로드하여 Teacher 객체 리스트로 반환"""
        df = pd.read_csv(f'{self.data_dir}/school_data.csv')
        # 교사명, 담당 교실만 추출 (중복 제거)
        teachers = df[['선생님', '담당 교실']].drop_duplicates()
        return [Teacher(row['선생님'], row['담당 교실']) for _, row in teachers.iterrows()]

    def load_locations(self) -> List[Location]:
        """위치 정보를 로드하여 Location 객체 리스트로 반환"""
        df = pd.read_csv(f'{self.data_dir}/locations.csv')
        return [Location(row['building'], int(row['floor']), row['room_number'], float(row['x_coord']), float(row['y_coord'])) for _, row in df.iterrows()]

    def load_csv(self, name):
        """CSV 파일을 DataFrame으로 로드"""
        return pd.read_csv(f'{self.data_dir}/{name}.csv')

    def load_json(self, name):
        """JSON 파일을 dict로 로드"""
        with open(f'{self.data_dir}/{name}.json', encoding='utf-8') as f:
            return json.load(f)

    def load_delivery_data(self, file_name='delivery_data.csv'):
        """
        배달 데이터를 로드하고 전처리
        
        Args:
            file_name (str): 배달 데이터 파일명
            
        Returns:
            pandas.DataFrame: 전처리된 배달 데이터
        """
        try:
            file_path = os.path.join(self.data_dir, file_name)
            
            # 파일이 존재하는지 확인
            if not os.path.exists(file_path):
                logger.error(f"배달 데이터 파일을 찾을 수 없음: {file_path}")
                return None
                
            # 파일 수정 시간 확인
            current_mtime = os.path.getmtime(file_path)
            if file_path in self.last_modified and current_mtime == self.last_modified[file_path]:
                logger.info("캐시된 배달 데이터 사용")
                return self.cache.get(file_path)
            
            # CSV 파일 로드
            df = pd.read_csv(file_path)
            
            # 필수 컬럼 확인
            required_columns = ['id', 'pickup_location', 'delivery_location', 'time_window']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                logger.error(f"필수 컬럼 누락: {missing_columns}")
                return None
            
            # 데이터 전처리
            df = self._preprocess_delivery_data(df)
            
            # 캐시 업데이트
            self.cache[file_path] = df
            self.last_modified[file_path] = current_mtime
            
            logger.info(f"배달 데이터 로드 완료: {len(df)}개 레코드")
            return df
            
        except Exception as e:
            logger.error(f"배달 데이터 로드 중 오류 발생: {str(e)}")
            return None

    def load_vehicle_data(self, file_name='vehicle_data.csv'):
        """
        차량 데이터를 로드하고 전처리
        
        Args:
            file_name (str): 차량 데이터 파일명
            
        Returns:
            pandas.DataFrame: 전처리된 차량 데이터
        """
        try:
            file_path = os.path.join(self.data_dir, file_name)
            
            # 파일이 존재하는지 확인
            if not os.path.exists(file_path):
                logger.error(f"차량 데이터 파일을 찾을 수 없음: {file_path}")
                return None
                
            # 파일 수정 시간 확인
            current_mtime = os.path.getmtime(file_path)
            if file_path in self.last_modified and current_mtime == self.last_modified[file_path]:
                logger.info("캐시된 차량 데이터 사용")
                return self.cache.get(file_path)
            
            # CSV 파일 로드
            df = pd.read_csv(file_path)
            
            # 필수 컬럼 확인
            required_columns = ['id', 'capacity', 'current_location']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                logger.error(f"필수 컬럼 누락: {missing_columns}")
                return None
            
            # 데이터 전처리
            df = self._preprocess_vehicle_data(df)
            
            # 캐시 업데이트
            self.cache[file_path] = df
            self.last_modified[file_path] = current_mtime
            
            logger.info(f"차량 데이터 로드 완료: {len(df)}개 레코드")
            return df
            
        except Exception as e:
            logger.error(f"차량 데이터 로드 중 오류 발생: {str(e)}")
            return None

    def _preprocess_delivery_data(self, df):
        """
        배달 데이터 전처리
        
        Args:
            df (pandas.DataFrame): 원본 배달 데이터
            
        Returns:
            pandas.DataFrame: 전처리된 배달 데이터
        """
        try:
            # 결측치 처리
            df = df.fillna({
                'priority': 0,  # 우선순위가 없는 경우 기본값 0
                'weight': 0,    # 무게가 없는 경우 기본값 0
                'volume': 0     # 부피가 없는 경우 기본값 0
            })
            
            # 시간대 데이터 변환
            if 'time_window' in df.columns:
                df['time_window'] = pd.to_datetime(df['time_window'])
            
            # 위치 데이터 정규화
            if 'pickup_location' in df.columns:
                df['pickup_location'] = df['pickup_location'].apply(self._normalize_location)
            if 'delivery_location' in df.columns:
                df['delivery_location'] = df['delivery_location'].apply(self._normalize_location)
            
            # 데이터 타입 변환
            df['id'] = df['id'].astype(str)
            df['priority'] = df['priority'].astype(int)
            df['weight'] = df['weight'].astype(float)
            df['volume'] = df['volume'].astype(float)
            
            return df
            
        except Exception as e:
            logger.error(f"배달 데이터 전처리 중 오류 발생: {str(e)}")
            return df

    def _preprocess_vehicle_data(self, df):
        """
        차량 데이터 전처리
        
        Args:
            df (pandas.DataFrame): 원본 차량 데이터
            
        Returns:
            pandas.DataFrame: 전처리된 차량 데이터
        """
        try:
            # 결측치 처리
            df = df.fillna({
                'capacity': 0,      # 용량이 없는 경우 기본값 0
                'fuel_level': 100,  # 연료 레벨이 없는 경우 기본값 100%
                'status': 'idle'    # 상태가 없는 경우 기본값 'idle'
            })
            
            # 위치 데이터 정규화
            if 'current_location' in df.columns:
                df['current_location'] = df['current_location'].apply(self._normalize_location)
            
            # 데이터 타입 변환
            df['id'] = df['id'].astype(str)
            df['capacity'] = df['capacity'].astype(float)
            df['fuel_level'] = df['fuel_level'].astype(float)
            
            return df
            
        except Exception as e:
            logger.error(f"차량 데이터 전처리 중 오류 발생: {str(e)}")
            return df

    def _normalize_location(self, location):
        """
        위치 데이터 정규화
        
        Args:
            location (str): 원본 위치 데이터
            
        Returns:
            str: 정규화된 위치 데이터
        """
        try:
            if pd.isna(location):
                return "unknown"
                
            # 문자열로 변환
            location = str(location).strip().lower()
            
            # 특수문자 제거
            location = ''.join(c for c in location if c.isalnum() or c.isspace())
            
            # 공백 정규화
            location = ' '.join(location.split())
            
            return location
            
        except Exception as e:
            logger.error(f"위치 데이터 정규화 중 오류 발생: {str(e)}")
            return "unknown"

    def save_data(self, data, file_name):
        """
        데이터를 파일로 저장
        
        Args:
            data (pandas.DataFrame): 저장할 데이터
            file_name (str): 저장할 파일명
            
        Returns:
            bool: 저장 성공 여부
        """
        try:
            file_path = os.path.join(self.data_dir, file_name)
            
            # 파일 확장자에 따라 저장 방식 결정
            if file_name.endswith('.csv'):
                data.to_csv(file_path, index=False)
            elif file_name.endswith('.json'):
                data.to_json(file_path, orient='records')
            elif file_name.endswith('.xlsx'):
                data.to_excel(file_path, index=False)
            else:
                logger.error(f"지원하지 않는 파일 형식: {file_name}")
                return False
            
            # 캐시 및 수정 시간 업데이트
            self.cache[file_path] = data
            self.last_modified[file_path] = os.path.getmtime(file_path)
            
            logger.info(f"데이터 저장 완료: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"데이터 저장 중 오류 발생: {str(e)}")
            return False

    def clear_cache(self):
        """데이터 캐시 초기화"""
        self.cache.clear()
        self.last_modified.clear()
        logger.info("데이터 캐시가 초기화되었습니다.") 