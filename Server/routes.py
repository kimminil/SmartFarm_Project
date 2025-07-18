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

CMD_TEMP = "NORMAL"
CMD_HUMI = "NORMAL"
CMD_CO2 = "NORMAL"
CMD_LIGHT = "NORMAL"
def weighted_loss(y_true, y_pred):
    weight = np.linspace(0.5, 1.5, num=y_true.shape[1])  # 마지막 값에 더 큰 가중치
    return K.mean(weight * K.square(y_pred - y_true))

def range_filter(current,prev,min_val,max_val):
    if current is None:
        return prev
    if current < min_val or current > max_val:
        return prev
    return current
try:
    
    with CustomObjectScope({'weighted_loss': weighted_loss}):
        co2_model =  tf.keras.models.load_model('training/CO2.h5')
    temp_model = tf.keras.models.load_model('./training/Temperature.h5')
    temp_scaler = joblib.load('./training/Temperature.pkl')
    humi_model = tf.keras.models.load_model('./training/humidity.h5')
    humi_scaler = joblib.load('./training/humidity.pkl')
    co2_model = tf.keras.models.load_model('./training/CO2.h5')
    co2_scaler = joblib.load('./training/CO2.pkl')

except Exception as e:
    print("모델 또는 스케일러 로드 실패:", e)
    temp_model = None
    temp_scaler = None
    humi_model = None
    humi_scaler = None
    co2_model = None
    co2_scaler = None

    
#테스트용 코드 구분
# 연속성을 가진 테스트 데이터 저장
@bp.route('/test/temp/insert')
def temps():
    base_temp = 20.0  # 기준 온도 (예: 20도)

    
    for _ in range(30):
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

    sub = (
        md.testData.query
        .with_entities(md.testData.temp,md.testData.id)
        .order_by(md.testData.id.desc())
        .limit(30)
        
    ).subquery()
    
    rows = (
        md.db.session.query(sub.c.temp,sub.c.id)
        .order_by(sub.c.id)
        .all()
        )
    
    temps = [t for t,_ in rows]
    prev = temps[0]
    filtered_temps = []
    for t in temps:
        filtered = range_filter(t,prev,5.0,40.0)
        filtered_temps.append(filtered)
        prev = filtered
        
    
    filtered_temps = np.array(filtered_temps).reshape(-1, 1)
    temp_scaled = temp_scaler.transform(filtered_temps) 

    # 6. LSTM 입력 형태 맞추기
    X_input = temp_scaled.reshape(1, 30, 1)

    # 7. 예측
    y_pred_scaled = temp_model.predict(X_input)

    # 8. 역변환
    y_pred = temp_scaler.inverse_transform(y_pred_scaled)
    print(f"예측된 다음 시점 온도: {y_pred[0][0]:.2f} ℃")
    return jsonify({
        "temp" : f"현재 저장된 10개의 온도 값: {filtered_temps}",
        "predict": f"{y_pred[0][0]:.2f}"
        })

@bp.route('/test/predict/humi',methods=['POST'])
def pred_humi():
    if humi_model is None or humi_scaler is None:
       return jsonify({"error": "모델 또는 스케일러가 로드되지 않았습니다."}), 500

    sub = (
        md.testData.query
        .with_entities(md.testData.humi,md.testData.id)
        .order_by(md.testData.id.desc())
        .limit(30)
        
        
    ).subquery()
    
    rows = (
        md.db.session.query(sub.c.humi,sub.c.id)
        .order_by(sub.c.id)
        .all()
        )
    
    humis = [t for t,_ in rows]
    prev = humis[0]
    filtered_humis = []
    for t in humis:
        filtered = range_filter(t,prev,5.0,40.0)
        filtered_humis.append(filtered)
        prev = filtered
        
    
    filtered_humis = np.array(filtered_humis).reshape(-1, 1)
    humi_scaled = humi_scaler.transform(filtered_humis) 

    # 6. LSTM 입력 형태 맞추기
    X_input = humi_scaled.reshape(1, 30, 1)

    # 7. 예측
    y_pred_scaled = humi_model.predict(X_input)

    # 8. 역변환
    y_pred = humi_scaler.inverse_transform(y_pred_scaled)

    return jsonify({
        "humi" : f"현재 저장된 10개의 습도 값: {humis}",
        "predict": f"{y_pred[0][0]:.2f}",

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
    prev = co2s[0]
    filtered_co2s = []
    for t in co2s:
        filtered = range_filter(t,prev,5.0,40.0)
        filtered_co2s.append(filtered)
        prev = filtered
        
    
    filtered_co2s = np.array(filtered_co2s).reshape(-1, 1)
    co2_scaled = co2_scaler.transform(filtered_co2s) 

    # 6. LSTM 입력 형태 맞추기
    X_input = co2_scaled.reshape(1, 30, 1)

    # 7. 예측
    y_pred_scaled = co2_model.predict(X_input)

    # 8. 역변환
    y_pred = co2_scaler.inverse_transform(y_pred_scaled)
    print(f"예측된 다음 시점 co2: {y_pred[0][0]:.2f} ppm")
    return jsonify({
        "co2" : f"{co2s}",
        "predict": f"{y_pred[0][0]:.2f}"
        })






@bp.route('/test/insert')
def test_insert():
    for i in range(1,100):
        
        entry = md.testData(
            temp = round(random.uniform(0, 40), 2),
            humi = round(random.uniform(50, 90), 2),
            co2 = random.randint(300,1200),
            light = random.randint(1000,6000)
            
        )
        md.db.session.add(entry)
    md.db.session.commit();
    return jsonify({'message': '테스트 저장 성공'})

@bp.route('/test/result',methods=['POST'])
def test_result():
    global CMD_TEMP
    global CMD_HUMI
    global CMD_LIGHT
    global CMD_CO2
    data = request.json

    #예측 데이터
    temp_json = pred_temp()
    humi_json = pred_humi()
    co2_json = pred_co2()

    
    co2_data = co2_json.get_json()
    temp_data = temp_json.get_json()
    humi_data = humi_json.get_json()

    
    temp_predict = float(temp_data.get("predict"))
    humi_predict = float(humi_data.get("predict"))
    co2_predict = float(co2_data.get("predict"))

    
    #현재 데이터
    temp_current = float(data['temp'])
    humi_current = float(data['humi'])
    co2_current = float(data['co2'])
    light_current = float(data['light'])
    
    #제어 명령 결정

    
    #가중 평균 보정
    weighted_temp = 0.7 * temp_current + 0.3 * temp_predict
    weighted_humi = 0.9 * humi_current + 0.1 * humi_predict
   
    weighted_co2 = 0.7 * co2_current + 0.3 * co2_predict
    TEMP_LOW = 12.0
    TEMP_HIGH = 28.0
    
    HUMI_LOW = 40.0
    HUMI_HIGH = 70.0
    
    LIGHT_LOW = 8000
    LIGHT_HIGH = 15000
    
    CO2_LOW = 300
    CO2_HIGH = 1000
    HYSTERESIS = 1.0
    if CMD_TEMP == "NORMAL":
        if temp_current >= TEMP_HIGH or weighted_temp >= TEMP_HIGH:
            CMD_TEMP = "DECREASE"   # 냉각 시작
        elif temp_current <= TEMP_LOW or weighted_temp <= TEMP_LOW:
            CMD_TEMP = "INCREASE"   # 난방 시작
    elif CMD_TEMP == "DECREASE":
        if temp_current < TEMP_HIGH - HYSTERESIS or weighted_temp < TEMP_HIGH - HYSTERESIS:
            CMD_TEMP = "NORMAL"
    elif CMD_TEMP == "INCREASE":
        if temp_current > TEMP_LOW + HYSTERESIS or weighted_temp > TEMP_LOW + HYSTERESIS:
            CMD_TEMP = "NORMAL"
    
    # 습도 FSM
    if CMD_HUMI == "NORMAL":
        if humi_current >= HUMI_HIGH or weighted_humi >= HUMI_HIGH:
            CMD_HUMI = "DECREASE"   # 습도 낮춤 (제습)
        elif humi_current <= HUMI_LOW or weighted_humi <= HUMI_LOW:
            CMD_HUMI = "INCREASE"   # 습도 올림 (가습)
    elif CMD_HUMI == "DECREASE":
        if humi_current < HUMI_HIGH - HYSTERESIS or weighted_humi < HUMI_HIGH - HYSTERESIS:
            CMD_HUMI = "NORMAL"
    elif CMD_HUMI == "INCREASE":
        if humi_current > HUMI_LOW + HYSTERESIS or weighted_humi > HUMI_LOW + HYSTERESIS:
            CMD_HUMI = "NORMAL"
    
    # CO2 FSM
    if CMD_CO2 == "NORMAL":
        if co2_current >= CO2_HIGH or weighted_co2 >= CO2_HIGH:
            CMD_CO2 = "DECREASE"   # 환기 (CO2 낮춤)
        elif co2_current <= CO2_LOW or weighted_co2 <= CO2_LOW:
            CMD_CO2 = "INCREASE"   # CO2 증가 (필요시)
    elif CMD_CO2 == "DECREASE":
        if co2_current < CO2_HIGH - HYSTERESIS or weighted_co2 < CO2_HIGH - HYSTERESIS:
            CMD_CO2 = "NORMAL"
    elif CMD_CO2 == "INCREASE":
        if co2_current > CO2_LOW + HYSTERESIS or weighted_co2 > CO2_LOW + HYSTERESIS:
            CMD_CO2 = "NORMAL"
    
    # 조도 FSM (실측값 기준)
    if CMD_LIGHT == "NORMAL":
        if light_current >= LIGHT_HIGH:
            CMD_LIGHT = "DECREASE"   # 차광
        elif light_current <= LIGHT_LOW:
            CMD_LIGHT = "INCREASE"   # 조명 증가
    elif CMD_LIGHT == "DECREASE":
        if light_current < (LIGHT_HIGH - HYSTERESIS):
            CMD_LIGHT = "NORMAL"
    elif CMD_LIGHT == "INCREASE":
        if light_current > (LIGHT_LOW + HYSTERESIS):
            CMD_LIGHT = "NORMAL"
    
    entry = md.testData(
        temp = data['temp'],
        humi = data['humi'],
        co2 = data['co2'],
        light = data['light'],
        cmd_temp = CMD_TEMP,
        cmd_humi = CMD_HUMI,
        cmd_co2 = CMD_CO2,
        cmd_light = CMD_LIGHT
        
    )
    md.db.session.add(entry)
    md.db.session.commit()
    
    return jsonify({
        'temp_predict' : f'{temp_predict}',
        'humi_predict' : f'{humi_predict}',
        'co2_predict' : f'{co2_predict}',
        
        
        #현재 데이터
        'temp_current' : f"{data['temp']}",
        'humi_current' : f"{data['humi']}",
        'co2_current' : f"{data['co2']}",
        'light_current' : f"{data['light']}",
        
        'CMD_TEMP' : f"{CMD_TEMP}",
        'CMD_HUMI' : f"{CMD_HUMI}",
        'CMD_LIGHT' : f"{CMD_LIGHT}",
        'CMD_CO2' : f"{CMD_CO2}"
        })
    
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
    md.db.session.commit()
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