import pandas as pd
import json
from models import Teacher, Location
from typing import List

class DataLoader:
    def __init__(self, data_dir='data'):
        self.data_dir = data_dir
        self.school_data = self.load_school_data()
        self.locations = self.load_locations()

    def load_school_data(self):
        df = pd.read_csv(f'{self.data_dir}/school_data.csv')
        return df.to_dict('records')

    def load_teachers(self) -> List[Teacher]:
        df = pd.read_csv(f'{self.data_dir}/school_data.csv')
        # 교사명, 담당 교실만 추출 (중복 제거)
        teachers = df[['선생님', '담당 교실']].drop_duplicates()
        return [Teacher(row['선생님'], row['담당 교실']) for _, row in teachers.iterrows()]

    def load_locations(self) -> List[Location]:
        df = pd.read_csv(f'{self.data_dir}/locations.csv')
        return [Location(row['building'], int(row['floor']), row['room_number'], float(row['x_coord']), float(row['y_coord'])) for _, row in df.iterrows()]

    def load_csv(self, name):
        """CSV 파일을 DataFrame으로 로드"""
        return pd.read_csv(f'{self.data_dir}/{name}.csv')

    def load_json(self, name):
        """JSON 파일을 dict로 로드"""
        with open(f'{self.data_dir}/{name}.json', encoding='utf-8') as f:
            return json.load(f) 