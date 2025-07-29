
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

rpi_url = "http://192.168.1.80:5050"
rpi2_url = "http://192.168.1.52:5050"

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
            logger.info(data)
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


# 카메라

#First Webcam
frame = [None]
frame2 = [None]
def mjpeg_generator(buffer):
    while True:
        if buffer[0] is not None:
            ret, jpeg = cv2.imencode('.jpg', buffer[0])
            if not ret:
                continue
            b = jpeg.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + b + b'\r\n')
        time.sleep(0.03)

@app.route('/video_feed')
def video_feed():
    return Response(mjpeg_generator(frame),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/video_feed2')
def video_feed2():
    return Response(mjpeg_generator(frame2),
                    mimetype='multipart/x-mixed-replace; boundary=frame')
# Webcam Reciecve
@app.route('/upload', methods=['POST'])
def upload_record():
    img_bytes = request.files['image'].read()
    nparr = np.frombuffer(img_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    frame[0] = img
    return 'OK'

@app.route('/upload2', methods=['POST'])
def upload_record2():
    img_bytes = request.files['image'].read()
    nparr = np.frombuffer(img_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    frame2[0] = img
    return 'OK'


# Webcam Page
@app.route('/camera')
def camera_page():
    global active_clients
    with streaming_lock:
        active_clients += 1
    requests.get(rpi_url + "/start_stream",timeout=1)
    requests.get(rpi2_url + "/start_stream",timeout=1)
    return render_template('second.html')

@app.route('/camera_close')
def camera_close():
    global active_clients
    with streaming_lock:
        if active_clients > 0:
            active_clients -= 1
    requests.get(rpi_url + "/stop_stream",timeout=1)
    requests.get(rpi2_url + "/stop_stream",timeout=1)
    return "Camera closed"  


#  image Test
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

# current Page
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
            socketio.sleep(60)



if __name__ == '__main__':
    socketio.start_background_task(background_task)

    socketio.run(app,
                 host='0.0.0.0',
                 port=5000,
                 debug=True,
                 use_reloader=False)  # 리로더 끄기
