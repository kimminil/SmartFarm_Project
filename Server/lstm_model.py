import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
import joblib



# 데이터 불러오기
df_train = pd.read_csv('DataTraining.csv')
df_test = pd.read_csv('DataTest.csv')

# 날짜 기준 파싱
df_train['date'] = pd.to_datetime(df_train['date'], dayfirst=True)
df_test['date'] = pd.to_datetime(df_test['date'], dayfirst=True)

# 인덱스 지정
df_train.set_index('date', inplace=True)
df_test.set_index('date', inplace=True)

# 온도 데이터만 추출
train_temp = df_train['Temperature']
test_temp = df_test['Temperature']

# numpy 배열로 변환 및 reshape (samples, 1)
train_values = train_temp.values.reshape(-1,1)
test_values = test_temp.values.reshape(-1,1)

# 스케일링 (MinMaxScaler)
scaler = MinMaxScaler()
train_scaled = scaler.fit_transform(train_values)
test_scaled = scaler.transform(test_values)

# 시계열 데이터셋 변환
def create_dataset(data, time_steps=10):
    X, y = [], []
    for i in range(len(data) - time_steps):
        X.append(data[i:(i+time_steps), 0])
        y.append(data[i+time_steps, 0])
    return np.array(X), np.array(y)

time_steps = 10
X_train, y_train = create_dataset(train_scaled, time_steps)



X_test, y_test = create_dataset(test_scaled, time_steps)

# LSTM reshape
X_train = X_train.reshape(X_train.shape[0], X_train.shape[1], 1)
X_test = X_test.reshape(X_test.shape[0], X_test.shape[1], 1)

# 훈련 검증셋 분리
X_train_final, X_val, y_train_final, y_val = train_test_split(
    X_train, y_train, test_size=0.15, shuffle=False)  

# LSTM 모델
model = Sequential([
    LSTM(50,activation = 'tanh', return_sequences=True, input_shape=(time_steps, 1)),
    Dropout(0.2),
    LSTM(50),
    Dropout(0.2),
    Dense(1)
])

model.compile(optimizer='adam', loss='mse',metrics=['mae'])

# 모델 학습
early_stop = EarlyStopping(monitor='val_loss', patience=10)
history = model.fit(X_train_final, y_train_final, validation_data=(X_val, y_val),
                    epochs=100, batch_size=32, callbacks=[early_stop])
model.save('Temperature.h5')
joblib.dump(scaler, 'scaler.pkl')
# 테스트 데이터 예측
test_loss, test_mae = model.evaluate(X_test, y_test)
print(f"Test Loss (MSE): {test_loss:.4f}")
print(f"Test MAE: {test_mae:.4f}")
y_pred_scaled = model.predict(X_test)

# 예측 결과 역스케일링
y_pred = scaler.inverse_transform(y_pred_scaled)
y_true = scaler.inverse_transform(y_test.reshape(-1,1))

# 결과 시각화
plt.figure(figsize=(12,6))
plt.plot(y_true, label='Actual Temperature')
plt.plot(y_pred, label='Predicted Temperature')
plt.title('Temperature Prediction on Test Data')
plt.xlabel('Time step')
plt.ylabel('Temperature')
plt.legend()
plt.show()
