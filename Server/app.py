
import eventlet
eventlet.monkey_patch()
from flask import Flask, request, jsonify,render_template,Response
import requests
from flask_socketio import SocketIO
from config import SQLALCHEMY_DATABASE_URI, SQLALCHEMY_TRACK_MODIFICATIONS
import models as md
from routes import bp as routes_bp
import os
import logging
from datetime import datetime, timedelta
from logging.handlers import RotatingFileHandler
import numpy as np
import cv2
import time
from sqlalchemy import func
from threading import Lock
from routes import pred_co2,pred_humi,pred_temp

streaming_lock = Lock()
sensor_entry_lock = Lock()
active_clients = 0

UPLOAD_FOLDER="./image"
os.makedirs(UPLOAD_FOLDER,exist_ok=True)

CMD_TEMP = "NORMAL"
CMD_HUMI = "NORMAL"
CMD_CO2 = "NORMAL"
CMD_LIGHT = "NORMAL"



app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = SQLALCHEMY_TRACK_MODIFICATIONS
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
socketio = SocketIO(app, cors_allowed_origins="*")
md.db.init_app(app)
app.register_blueprint(routes_bp)

log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler = RotatingFileHandler('app.log', maxBytes=5 * 1024 * 1024, backupCount=3, encoding='utf-8')
file_handler.setFormatter(log_formatter)
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)
logger.addHandler(console_handler)


last_sensor_entry = None
def select_db():
    try:
        last_record = (
            md.db.session.query(md.record_data)
            .order_by(md.record_data.No.desc())
            .first()
        )
        if last_record:
            data = last_record.to_dict()
            log_time = data.get('log_time')
            if log_time:
                data['timestamp'] = log_time.isoformat()
                del data['log_time']
            socketio.emit('sensor_update', data)
        else:
            logger.info("select_db: No record found.")
    except Exception as e:
        logger.error("select_db error: %s", e)
    finally:
        md.db.session.remove()  

@app.route('/record_data/sensor_insert',methods=['POST'])
def sensor_data():
    global last_sensor_entry
    data = request.json
    with sensor_entry_lock:
        last_sensor_entry = {
           'log_time': data['log_time'],
            'temp': data['temp'],
            'humi': data['humi'],
            'co2': data['co2'],
            'light': data['light'],
            'w_height': data['w_height'],
            
        }
    socketio.emit('sensor_update', last_sensor_entry)
    return jsonify({'msg':'update'})
    


frame = [None]
def mjpeg_generator():
    while True:
        if frame[0] is not None:
            ret, jpeg = cv2.imencode('.jpg',frame[0])
            
            if not ret: continue
            b = jpeg.tobytes()
            yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n'+b+b'\r\n')
        time.sleep(0.03)
@app.route('/upload', methods=['POST'])
def upload_record():
    global active_clients
    if active_clients == 0:
       return 'Camera not active', 403
    img_bytes = request.files['image'].read()
    nparr = np.frombuffer(img_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    frame[0] = img
    return 'OK'

@app.route('/video_feed')
def video_feed():
    return Response(mjpeg_generator(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')
@app.route('/camera')
def camera_page():
    global active_clients
    with streaming_lock:
        active_clients += 1
    requests.get('http://192.168.1.61:5050/start_stream',timeout=1)
    return render_template('second.html')

@app.route('/camera_close')
def camera_close():
    global active_clients
    with streaming_lock:
        if active_clients > 0:
            active_clients -= 1
    requests.get('http://192.168.1.61:5050/stop_stream',timeout=1)
    return "Camera closed"  

@app.route('/uploads', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        return jsonify({'error': 'No image part in the request'}), 400

    file = request.files['image']

    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    save_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(save_path)

    return jsonify({'message': f'Image saved to {save_path}'}), 200

@app.route('/api/today')
def get_today_data():
    try:
        today = datetime.now()
        start_time = today.replace(hour=0, minute=0, second=0, microsecond=0)
        end_time = today
        result = (
            md.record_data.query
            .filter(md.record_data.log_time.between(start_time, end_time))
            .order_by(md.record_data.log_time)
        ).all()
        result_dicts = [r.to_dict() for r in result]
        print(result_dicts)
        return jsonify(result_dicts)
    except Exception as e:
        logger.error(f"Today API 오류: {e}", exc_info=True)
        return jsonify({"error": "오류 발생"}), 500

# --- Socket.IO 이벤트 핸들러 ---
@socketio.on('connect')
def handle_connect(): 
    logger.info('클라이언트가 연결되었습니다.')
    select_db()

@socketio.on('disconnect')
def handle_disconnect(): 
    logger.info('클라이언트의 연결이 끊어졌습니다.')


   
@app.route('/')
def home():
  
    return render_template('index.html')

def background_task():
    # 1) 여기서 컨텍스트를 활성화
    with app.app_context():
        while True:
            try:
                select_db()
                print("▶ background tick")  

            except Exception as e:
                print("background_task error:", e)
            socketio.sleep(1)

def data_insert():
    global last_sensor_entry
    global CMD_TEMP, CMD_HUMI, CMD_LIGHT, CMD_CO2
    with app.app_context():
        while True:
            logger.info("BackgroundDB 실행")
            try:
                entry_copy = None
                with sensor_entry_lock:
                    if last_sensor_entry:
                        entry_copy = last_sensor_entry.copy()
                        
                if entry_copy:
             
  
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
                    temp_current = float(last_sensor_entry['temp'])
                    humi_current = float(last_sensor_entry['humi'])
                    co2_current = float(last_sensor_entry['co2'])
                    light_current = float(last_sensor_entry['light'])
                    
                    #제어 명령 결정
                
                    
                    #가중 평균 보정
                    weighted_temp = 0.7 * temp_current + 0.3 * temp_predict
                    weighted_humi = 0.9 * humi_current + 0.1 * humi_predict
                   
                    weighted_co2 = 0.7 * co2_current + 0.3 * co2_predict
                    TEMP_LOW = 12.0
                    TEMP_HIGH = 28.0
                    
                    HUMI_LOW = 40.0
                    HUMI_HIGH = 70.0
                    
                    LIGHT_LOW = 1.0
                    LIGHT_HIGH = 45.0
                    
                    CO2_LOW = 2000
                    CO2_HIGH = 3500
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
                    
                    entry = md.record_data(
                        log_time = entry_copy['log_time'],
                        temp = entry_copy['temp'],
                        humi = entry_copy['humi'],
                        co2 = entry_copy['co2'],
                        light = entry_copy['light'],
                        w_height = entry_copy['w_height'],    
                        cmd_temp_peltier = CMD_TEMP,
                        cmd_fan = CMD_HUMI,
                        cmd_light = CMD_LIGHT,
                        cmd_co2_vent = CMD_CO2
                    )
    
     
                    logger.info("DB접근")
                    
                    md.db.session.add(entry)
                    md.db.session.commit()


            except Exception as e:
                print("background_task error:", e)

            logger.info("BackgroundDB 실행")
            socketio.sleep(60)

if __name__ == '__main__':
    socketio.start_background_task(background_task)
    socketio.start_background_task(data_insert)
    socketio.run(app,
                 host='0.0.0.0',
                 port=5000,
                 debug=True,
                 use_reloader=False)  # 리로더 끄기
