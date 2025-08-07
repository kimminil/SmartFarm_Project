import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout,GRU
from tensorflow.keras.callbacks import EarlyStopping
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
import joblib
import os

# 데이터 불러오기
df_train = pd.read_csv('DataTraining.csv')
df_test = pd.read_csv('DataTest.csv')

# 날짜 파싱
df_train['date'] = pd.to_datetime(df_train['date'], dayfirst=True)
df_test['date'] = pd.to_datetime(df_test['date'], dayfirst=True)
df_train.set_index('date', inplace=True)
df_test.set_index('date', inplace=True)

# CO2 데이터만 추출
train_co2 = df_train['CO2'].values.reshape(-1,1)
test_co2 = df_test['CO2'].values.reshape(-1,1)

# 스케일링 (train만 fit, test는 transform)
scaler = MinMaxScaler()
train_scaled = scaler.fit_transform(train_co2)
test_scaled = scaler.transform(test_co2)

# 시계열 데이터셋 생성 함수
def create_dataset(data, time_steps):
    X, y = [], []
    for i in range(len(data) - time_steps):
        X.append(data[i:(i+time_steps), 0])
        y.append(data[i+time_steps, 0])
    return np.array(X), np.array(y)

time_steps = 30
X_train, y_train = create_dataset(train_scaled, time_steps)
X_test, y_test = create_dataset(test_scaled, time_steps)

# GRU 입력 shape 맞추기
X_train = X_train.reshape(-1, time_steps, 1)
X_test = X_test.reshape(-1, time_steps, 1)

# 훈련/검증 분리
X_train_final, X_val, y_train_final, y_val = train_test_split(
    X_train, y_train, test_size=0.15, shuffle=False)

# GRU 모델 (기본 MSE 손실함수 사용)
model = Sequential([
   LSTM(64, return_sequences=True, input_shape=(time_steps, 1)),
   LSTM(32),
   Dense(32, activation='relu'),
   Dropout(0.3),
   Dense(1)
])
model.compile(optimizer='adam', loss='mse', metrics=['mae'])

# 조기 종료 콜백
early_stop = EarlyStopping(monitor='val_loss', patience=3, restore_best_weights=True)
history = model.fit(
    X_train_final, y_train_final,
    validation_data=(X_val, y_val),
    epochs=100, batch_size=32, callbacks=[early_stop]
)

# 모델 저장
#model.save('CO2.h5')
#joblib.dump(scaler, 'CO2.pkl')

# 테스트 데이터 예측
test_loss, test_mae = model.evaluate(X_test, y_test)
print(f"Test Loss (MSE): {test_loss:.4f}")
print(f"Test MAE: {test_mae:.4f}")

y_pred_scaled = model.predict(X_test)

# 예측 결과 역스케일링
y_pred = scaler.inverse_transform(y_pred_scaled)
y_true = scaler.inverse_transform(y_test.reshape(-1,1))

# 결과 시각화
plt.figure(figsize=(12,5))
plt.plot(y_true[-100:], label="Actual")
plt.plot(y_pred[-100:], label="Predicted")
plt.legend(); plt.show()
