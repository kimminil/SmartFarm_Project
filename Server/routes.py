from flask import Blueprint, request, jsonify
import models as md
import random
import numpy as np
import joblib
from sklearn.preprocessing import MinMaxScaler
import tensorflow as tf
from tensorflow.keras.utils import CustomObjectScope
import tensorflow.keras.backend as K
bp = Blueprint('routes', __name__)

import os
print(os.getcwd())

def weighted_loss(y_true, y_pred):
    weight = np.linspace(0.5, 1.5, num=y_true.shape[1])  # 마지막 값에 더 큰 가중치
    return K.mean(weight * K.square(y_pred - y_true))
try:
    
    with CustomObjectScope({'weighted_loss': weighted_loss}):
        co2_model =  tf.keras.models.load_model('training/CO2.h5')
    temp_model = tf.keras.models.load_model('./training/Temperature.h5')
    temp_scaler = joblib.load('./training/Temperature.pkl')
    humi_model = tf.keras.models.load_model('./training/humidity.h5')
    humi_scaler = joblib.load('./training/humidity.pkl')
    #co2_model = tf.keras.models.load_model('./training/CO2.h5')
    co2_scaler = joblib.load('./training/CO2.pkl')
    light_model = tf.keras.models.load_model('./training/Light.h5')
    light_scaler = joblib.load('./training/Light.pkl')
except Exception as e:
    print("모델 또는 스케일러 로드 실패:", e)
    temp_model = None
    temp_scaler = None
    humi_model = None
    humi_scaler = None
    co2_model = None
    co2_scaler = None
    light_model = None
    light_scaler = None
# 연속성을 가진 테스트 데이터 저장
@bp.route('/test/temp/insert')
def temps():
    base_temp = 20.0  # 기준 온도 (예: 20도)

    
    for _ in range(29):
        # 이전 온도에서 -2도 ~ +2도 사이 변화 추가
        change = np.random.uniform(-2, 2)
        base_temp = base_temp + change
        
        # 온도 범위를 10~35도로 제한 (극단값 방지)
        base_temp = max(10, min(35,base_temp))

        entry = md.testData(
            temp = round(base_temp, 2),
            humi = round(random.uniform(50, 90), 2),
            co2 = 0,
            light = random.randint(1000,6000)
            
        )
        md.db.session.add(entry)
    md.db.session.commit();
    return jsonify({'message': '테스트 저장 성공'})

@bp.route('/test/co2/insert')
def ts():
    a=0
    dt=400
    for i in range(50):
        dt = dt+a;
        a = random.randint(1,30);
        entry = md.testData(
            temp = round(random.uniform(15, 30), 2),
            humi = round(random.uniform(50, 90), 2),
            co2 = dt,
            light = random.randint(1000,6000)
            
        )
        md.db.session.add(entry)
    md.db.session.commit();
    return jsonify({'message': '테스트 저장 성공'})
        
# 테스트 데이터 예측 현재 온도, co2만 만들어 놓음
@bp.route('/test/predict/temp',methods=['POST'])
def pred_temp():
    if temp_model is None or temp_scaler is None:
       return jsonify({"error": "모델 또는 스케일러가 로드되지 않았습니다."}), 500

    rows = (
        md.testData.query
        .with_entities(md.testData.temp,md.testData.id)
        .order_by(md.testData.id.desc())
        .limit(30)
        .all()
    )
    temps = [t for t,_ in rows]
    
    
    temps = np.array(temps).reshape(-1, 1)
    temp_scaled = temp_scaler.transform(temps) 

    # 6. LSTM 입력 형태 맞추기
    X_input = temp_scaled.reshape(1, 30, 1)

    # 7. 예측
    y_pred_scaled = temp_model.predict(X_input)

    # 8. 역변환
    y_pred = temp_scaler.inverse_transform(y_pred_scaled)
    print(f"예측된 다음 시점 온도: {y_pred[0][0]:.2f} ℃")
    return jsonify({
        "temp" : f"현재 저장된 10개의 온도 값: {temps}",
        "predict": f"예측된 다음 시점 온도: {y_pred[0][0]:.2f} ℃"
        })

@bp.route('/test/predict/humi',methods=['POST'])
def pred_humi():
    if humi_model is None or humi_scaler is None:
       return jsonify({"error": "모델 또는 스케일러가 로드되지 않았습니다."}), 500

    rows = (
        md.testData.query
        .with_entities(md.testData.humi,md.testData.id)
        .order_by(md.testData.id.desc())
        .limit(10)
        .order_by(md.testData.id)
        .all()
    )
    humis = [t for t,_ in rows]
    
    
    humis = np.array(humis).reshape(-1, 1)
    humi_scaled = humi_scaler.transform(humis) 

    # 6. LSTM 입력 형태 맞추기
    X_input = humi_scaled.reshape(1, 10, 1)

    # 7. 예측
    y_pred_scaled = humi_model.predict(X_input)

    # 8. 역변환
    y_pred = humi_scaler.inverse_transform(y_pred_scaled)
 
    return jsonify({
        "humi" : f"현재 저장된 10개의 습도 값: {humis}",
        "predict": f"예측된 다음 시점 습도: {y_pred[0][0]:.2f} %"
        })


@bp.route('/test/predict/co2',methods=['POST'])
def pred_co2():
    if co2_model is None or co2_scaler is None:
       return jsonify({"error": "모델 또는 스케일러가 로드되지 않았습니다."}), 500

    sub = (
        md.testData.query
        .with_entities(md.testData.co2,md.testData.id)
        .order_by(md.testData.id.desc())
        .limit(30)
        
    ).subquery()
    
    rows = (
        md.db.session.query(sub.c.co2,sub.c.id)
        #.order_by(sub.c.id)
        .all()
        )
    co2s = [t for t,_ in rows]
    
    
    co2s = np.array(co2s).reshape(-1, 1)
    co2_scaled = co2_scaler.transform(co2s) 

    # 6. LSTM 입력 형태 맞추기
    X_input = co2_scaled.reshape(1, 30, 1)

    # 7. 예측
    y_pred_scaled = co2_model.predict(X_input)

    # 8. 역변환
    y_pred = co2_scaler.inverse_transform(y_pred_scaled)
    
    return jsonify({
        "co2" : f"현재 저장된 10개의 co2 값: {co2s}",
        "predict": f"예측된 다음 시점 co2 값: {y_pred[0][0]:.2f} ppm"
        })


@bp.route('/test/predict/light',methods=['POST'])
def pred_light():
    if light_model is None or light_scaler is None:
       return jsonify({"error": "모델 또는 스케일러가 로드되지 않았습니다."}), 500

    rows = (
        md.testData.query
        .with_entities(md.testData.light,md.testData.id)
        .order_by(md.testData.id.desc())
        .limit(10)
        .all()
    )
    if len(rows) < 10:
       return jsonify({"error": "예측에 필요한 조도 데이터가 부족합니다 (10개 필요)."}), 400
    lights = [t for t,_ in rows]
    
    
    lights = np.array(lights).reshape(-1, 1)
    light_scaled = light_scaler.transform(lights) 

    # 6. LSTM 입력 형태 맞추기
    X_input = light_scaled.reshape(1, 10, 1)

    # 7. 예측
    y_pred_scaled = light_model.predict(X_input)

    # 8. 역변환
    y_pred = light_scaler.inverse_transform(y_pred_scaled)
    print(f"예측된 다음 시점 조도: {y_pred[0][0]:.2f} ℃")
    return jsonify({
        "light" : f"현재 저장된 10개의 조도 값: {lights}",
        "predict": f"예측된 다음 시점 조도: {y_pred[0][0]:.2f} lux"
        })


#테스트용 코드 구분
@bp.route('/test/insert')
def test_insert():
    for i in range(1,100):
        
        entry = md.testData(
            temp = round(random.uniform(15, 30), 2),
            humi = round(random.uniform(50, 90), 2),
            co2 = random.randint(300,1200),
            light = random.randint(1000,6000)
            
        )
        md.db.session.add(entry)
    md.db.session.commit();
    return jsonify({'message': '테스트 저장 성공'})
#테스트용 코드 구분
@bp.route('/init-db')
def init_db():
    md.db.create_all()
    return "✅ DB 초기화 완료"



@bp.route('/record_data/insert',methods=['POST'])
def data_insert():
    data = request.json
    entry = md.record_data(
        log_time = data['log_time'],
        temp = data['temp'],
        humi = data['humi'],
        co2 = data['co2'],
        light = data['light'],
        w_height = data['w_height']
        
    )
    md.db.session.add(entry)
    md.db.session.commit();
    return jsonify({'message': '센서 저장 성공'})

@bp.route('/record_access/insert',methods=['POST'])
def access_insert():
    data = request.json
    entry = md.record_access(
        access_time = data['access_time']
        )
    md.db.sesssion.add(entry)
    md.db.session.commit();
    return jsonify({'message': '로그 저장 성공'})
@bp.route('/position/insert',methods=['POST'])
def posi_insert():
    data = request.json
    entry = md.record_access(
        product_posi = data['product_posi'],
        status = data['status']
        )
    md.db.sesssion.add(entry)
    md.db.session.commit();
    return jsonify({'message': '위치 저장 성공'})
'''



@bp.route('/insert', methods=['POST'])
def insert_data():
    data = request.json
    entry = testData(
        email=data['email'],
        pwd=data['pwd']
    )
    db.session.add(entry)
    db.session.commit()
    return jsonify({'message': '삽입 성공'})

@bp.route('/data', methods=['GET'])
def get_all():
    rows = testData.query.all()
    return jsonify([
        {
            'id': r.id,
            'email': r.email,
            'pwd': r.pwd
        } for r in rows
    ])

@bp.route('/data/<int:data_id>', methods=['PUT'])
def update_data(data_id):
    data = request.json
    entry = testData.query.get(data_id)
    if entry:
        entry.email = data['email']
        entry.pwd = data['pwd']
        db.session.commit()
        return jsonify({'message': '수정 완료'})
    return jsonify({'message': '데이터 없음'}), 404

@bp.route('/data/<int:data_id>', methods=['DELETE'])
def delete_data(data_id):
    entry = testData.query.get(data_id)
    if entry:
        db.session.delete(entry)
        db.session.commit()
        return jsonify({'message': '삭제 완료'})
    return jsonify({'message': '데이터 없음'}), 404
'''