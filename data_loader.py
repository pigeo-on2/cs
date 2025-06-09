# 필요한 라이브러리 임포트
import pandas as pd
import json
from models import Teacher, Location
from typing import List

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