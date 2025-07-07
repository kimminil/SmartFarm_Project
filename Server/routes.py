from flask import Blueprint, request, jsonify
import models as md
import random
import numpy as np
import joblib
from sklearn.preprocessing import MinMaxScaler
import tensorflow as tf
bp = Blueprint('routes', __name__)

@bp.route('/test/predict',methods=['POST'])
def pred():
    model = tf.keras.models.load_model('./training/Temperature.h5')

    rows = (
        md.testData.query
        .with_entities(md.testData.temp,md.testData.id)
        .order_by(md.testData.id.desc())
        .limit(10)
        .all()
    )
    temps = [t for t,_ in rows]
    
    scaler = joblib.load('./training/Temperature.pkl') 
    temps = np.array(temps).reshape(-1, 1)
    temp_scaled = scaler.transform(temps) 

    # 6. LSTM 입력 형태 맞추기
    X_input = temp_scaled.reshape(1, 10, 1)

    # 7. 예측
    y_pred_scaled = model.predict(X_input)

    # 8. 역변환
    y_pred = scaler.inverse_transform(y_pred_scaled)
    print(f"예측된 다음 시점 온도: {y_pred[0][0]:.2f} ℃")
    return jsonify({
        "temp" : f"현재 저장된 10개의 온도 값: {temps}",
        "predict": f"예측된 다음 시점 온도: {y_pred[0][0]:.2f} ℃"
        })


#테스트용 코드 구분
@bp.route('/test/insert')
def test_insert():
    for i in range(1,100):
        data = md.testData(temp=random.randint(20, 40))
        md.db.session.add(data)
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