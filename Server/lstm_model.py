import pandas as pd


df = pd.read_csv('greenhouse.csv', sep=';')
print(df.head())      # 상위 5개 행 출력
print(df.columns)     # 컬럼명 확인
print(df.info())      # 데이터 타입, 결측치 등 확인