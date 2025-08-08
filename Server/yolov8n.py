import eventlet
eventlet.monkey_patch()

#서버
from flask import Flask, request, jsonify, render_template, Response
from flask_socketio import SocketIO
from routes import bp as routes_bp
import requests

#DB
import models as md
from config import SQLALCHEMY_DATABASE_URI, SQLALCHEMY_TRACK_MODIFICATIONS

#시스템
import os
from datetime import datetime, timedelta
from threading import Lock
import time

#로그
import logging
from logging.handlers import RotatingFileHandler

#YOLO
from PIL import ImageFont, ImageDraw, Image
import numpy as np
import cv2
import torch
from ultralytics.nn import tasks
from torch.nn.modules.container import Sequential
from ultralytics.nn.modules.conv import Conv
from torch.nn.modules.conv import Conv2d
from ultralytics import YOLO
try:
    torch.serialization.add_safe_globals([tasks.DetectionModel, Sequential, Conv, Conv2d])
except AttributeError:
    pass



yolo_model = YOLO('best.pt')

streaming_lock = Lock()
sensor_entry_lock = Lock()
active_clients = 0

UPLOAD_FOLDER = "./image"
UPLOAD_FOLDER_2 = "./image1"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(UPLOAD_FOLDER_2, exist_ok=True)


rpi_url = "http://192.168.1.108:5050"
rpi2_url = "http://192.168.1.102:5050"

CMD_TEMP = "NORMAL"
CMD_HUMI = "NORMAL"
CMD_CO2 = "NORMAL"
CMD_LIGHT = "NORMAL"

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = SQLALCHEMY_TRACK_MODIFICATIONS
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['UPLOAD_FOLDER_2'] = UPLOAD_FOLDER_2


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

sensor_flag = False
camera_flag = False
control_flag = False
YOLO_MODE = False
num = 0

# ---- 카메라 프레임 버퍼 ----
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



class_names = ["빈통", "생장중", "수확"]

@app.route('/upload', methods=['POST'])
def upload_record():
    pos = {1:340,2:640}
    pos_dict = {f"pos{k}":0 for k in range(1,3)}
    best_for_pos1 = {i:{'conf':0, 'class_id':None,'box':None} for i in pos}
    if camera_flag:
        img_bytes = request.files['image'].read()
        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        img = cv2.flip(img, -1)
        h, w = img.shape[:2]
        crop_ratio = np.sqrt(0.55)  # sqrt(0.2) = 대략 44.7%
        crop_w = int(w * crop_ratio)
        crop_h = int(h * crop_ratio)
        center_x = w // 2
        center_y = h // 2
        x1 = max(center_x - crop_w // 2, 0)
        x2 = min(center_x + crop_w // 2, w)
        y1 = max(center_y - crop_h // 2, 0)
        y2 = min(center_y + crop_h // 2, h)
        crop = img[y1:y2, x1:x2]
        zoomed = cv2.resize(crop, (w, h), interpolation=cv2.INTER_LINEAR)
        if YOLO_MODE:
            results = yolo_model(zoomed,conf=0.35,iou=0.3)
            #results = yolo_model(img,conf=0.35,iou=0.3)
            img_pil = Image.fromarray(cv2.cvtColor(zoomed, cv2.COLOR_BGR2RGB))
            draw = ImageDraw.Draw(img_pil)
            font = ImageFont.truetype(r"C:\Windows\Fonts\malgun.ttf", 30)  
            
            for i in results:
                for box in i.boxes:
                    conf = float(box.conf[0])
                    class_id = int(box.cls[0])
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    center_x = (x1+x2)/2
                    for j in pos:
                        if pos[j] >= center_x - 15 and pos[j]<=center_x +15:
                            if conf>best_for_pos1[j]['conf']:
                                best_for_pos1[j] = {'conf':conf, 'class_id':class_id,'box':(x1,y1,x2,y2)}
                    label = class_names[class_id]
                    draw.rectangle([x1, y1, x2, y2], outline=(0,255,0), width=3)
                    draw.text((x1, y1-35), f"{label} {center_x} {conf:.2f}", font=font, fill=(0,255,0,0))
            zoomed = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
            frame[0] = zoomed
        else:
            frame[0] = zoomed
        return 'OK'
    else:
        return 'error'

@app.route('/upload2', methods=['POST'])
def upload_record2():
    pos = {1:350,2:610}
    pos_dict = {f"pos{k}":0 for k in range(1,3)}
    best_for_pos1 = {i:{'conf':0, 'class_id':None,'box':None} for i in pos}
    if camera_flag:
        img_bytes = request.files['image'].read()
        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        img = cv2.flip(img, -1)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        img = cv2.flip(img, -1)
        h, w = img.shape[:2]
        crop_ratio = np.sqrt(0.55)  # sqrt(0.2) = 대략 44.7%
        crop_w = int(w * crop_ratio)
        crop_h = int(h * crop_ratio)
        center_x = w // 2
        center_y = h // 2
        x1 = max(center_x - crop_w // 2, 0)
        x2 = min(center_x + crop_w // 2, w)
        y1 = max(center_y - crop_h // 2, 0)
        y2 = min(center_y + crop_h // 2, h)
        crop = img[y1:y2, x1:x2]
        zoomed = cv2.resize(crop, (w, h), interpolation=cv2.INTER_LINEAR)
        if YOLO_MODE:
            results = yolo_model(zoomed,conf=0.45,iou=0.3)
            
            img_pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
            draw = ImageDraw.Draw(img_pil)
            font = ImageFont.truetype(r"C:\Windows\Fonts\malgun.ttf", 30)  
            
            for i in results:
                for box in i.boxes:
                    conf = float(box.conf[0])
                    class_id = int(box.cls[0])
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    
                    center_x = (x1+x2)/2
                    for j in pos:
                        if pos[j] >= center_x - 15 and pos[j]<=center_x +15:
                            if conf>best_for_pos1[j]['conf']:
                                best_for_pos1[j] = {'conf':conf, 'class_id':class_id,'box':(x1,y1,x2,y2)}
                    label = class_names[class_id]
                    draw.rectangle([x1, y1, x2, y2], outline=(0,255,0), width=3)
                    draw.text((x1, y1-35), f"{label} {center_x} {conf:.2f}", font=font, fill=(0,255,0,0))
            
            img = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
            frame2[0] = img

        else:
            frame2[0] = img

        return 'OK'
    else:
        return 'error'

@app.route('/camera')
def camera_page():
    global sensor_flag, camera_flag, active_clients, YOLO_MODE

    if sensor_flag:
        sensor_flag = False
    
    if not camera_flag:
        with streaming_lock:
            active_clients += 1
        success = False
        error_msgs = []
        for url in (rpi_url, rpi2_url):
            try:
                resp = requests.get(f"{url}/start_stream", timeout=2)
                if resp.status_code == 200:
                    success = True
                else:
                    error_msgs.append(f"{url} returned {resp.status_code}")
            except Exception as e:
                error_msgs.append(f"{url} error: {e}")
        if not success:
            for url in (rpi_url, rpi2_url):
                try:
                    requests.get(f"{url}/stop_stream", timeout=1)
                except:
                    pass
            with streaming_lock:
                active_clients = max(active_clients - 1, 0)
            return jsonify({"status": "error", "message": "raspberrypi access failed", "details": error_msgs}), 503
        camera_flag = True
    
    YOLO_MODE = True
    return render_template('yolov8n.html')

@app.route('/manual')
def second_page():
    global sensor_flag, control_flag
    print(sensor_flag, control_flag)
    if sensor_flag:
        sensor_flag = False
    if not control_flag:
        control_flag = True
    
    return render_template('manual_operation.html')

@app.route('/camera_close')
def camera_close():
    global active_clients, sensor_flag, camera_flag
    if not sensor_flag:
        sensor_flag = True
    if camera_flag:
        camera_flag = False
        with streaming_lock:
            active_clients = max(active_clients - 1, 0)
        for url in (rpi_url, rpi2_url):
            try:
                requests.get(f"{url}/stop_stream", timeout=1)
            except:
                pass
        return "Camera closed"
    else:
        return "Camera already closed"






@app.route('/uploads', methods=['POST'])
def upload_image():
    global sensor_flag
    if sensor_flag:
        pos = {1:350,2:610,3:748}
        best_for_pos1 = {i:{'conf':0, 'class_id':None,'box':None} for i in pos}
        pos_dict = {f"pos{k}":0 for k in range(1,4)}
        if 'image' not in request.files:
            return jsonify({'error': 'No image part in the request'}), 400
        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
    
        
        img_bytes = file.read()
        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        img = cv2.flip(img, -1)
        
        
        results = yolo_model(img,conf=0.45,iou=0.3)
        
        
        img_pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(img_pil)
        
        font = ImageFont.truetype(r"C:\Windows\Fonts\malgun.ttf", 30)
        
        for i in results:
            for box in i.boxes:
                class_id = int(box.cls[0])
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                conf = float(box.conf[0])
                center_x = (x1+x2)/2
                for j in pos:
                    if pos[j] >= center_x - 15 and pos[j]<=center_x +15:
                        if conf>best_for_pos1[j]['conf']:
                            best_for_pos1[j] = {'conf':conf, 'class_id':class_id,'box':(x1,y1,x2,y2)}
                label = class_names[class_id]
                draw.rectangle([x1, y1, x2, y2], outline=(0,255,0), width=3)
                draw.text((x1, y1-35), f"{label} {center_x} {conf:.2f}", font=font, fill=(0,255,0,0))
        for j in pos:
            if best_for_pos1[j]['conf']>0:
                class_id = best_for_pos1[j]['class_id']
                pos_dict[f"pos{j}"] = 1 if class_names[class_id] == "수확" else 0
                
        img_result = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
        success = md.record_product_condition.update_data(md.db.session, pos_dict)
        print(pos_dict)
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        cv2.imwrite(save_path, img_result)  # 여기서 OpenCV로 저장
    
        return jsonify({'message': f'Image saved to {save_path}'}), 200

    else:
        return jsonify({'message': f'wait'}), 500
@app.route('/uploads2', methods=['POST'])
def upload_image2():
    global sensor_flag
    if sensor_flag:
        pos = {3:430,4:645}
        pos_dict = {f"pos2{k}":0 for k in range(3,5)}
        
        best_for_pos2 = {i:{'conf':0, 'class_id':None,'box':None} for i in pos}
        
        if 'image' not in request.files:
            return jsonify({'error': 'No image part in the request'}), 400
        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        file.filename = 'frame2.jpg'
        
        img_bytes = file.read()
        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        img = cv2.flip(img, -1)
        
        
        results = yolo_model(img,conf=0.45,iou=0.3)
        
        
        img_pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(img_pil)
        
        font = ImageFont.truetype(r"C:\Windows\Fonts\malgun.ttf", 30)
        
        for i in results:
            for box in i.boxes:
                class_id = int(box.cls[0])
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                conf = float(box.conf[0])
                center_x = (x1+x2)/2
                for j in pos:
                    if pos[j] >= center_x - 15 and pos[j]<=center_x +15:
                        if conf>best_for_pos2[j]['conf']:
                            best_for_pos2[j] = {'conf':conf, 'class_id':class_id,'box':(x1,y1,x2,y2)}
                label = class_names[class_id]
                draw.rectangle([x1, y1, x2, y2], outline=(0,255,0), width=3)
                draw.text((x1, y1-35), f"{label} {center_x} {conf:.2f}", font=font, fill=(0,255,0,0))
        for j in pos:
            if best_for_pos2[j]['conf']>0:
                class_id = best_for_pos2[j]['class_id']
                pos_dict[f"pos{j}"] = 1 if class_names[class_id] == "수확" else 0
                
                
        img_result = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
        success = md.record_product_condition.update_data(md.db.session, pos_dict)
        print(pos_dict)
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        cv2.imwrite(save_path, img_result)  # 여기서 OpenCV로 저장
    
        return jsonify({'message': f'Image saved to {save_path}'}), 200
    else:
        return "wait.."
    
@app.route('/api/today')
def get_today_data():
    today = datetime.now()
    #start_time = (today - timedelta(days=2)).replace(hour=23, minute=0, second=0, microsecond=0)
    
    #end_time = (today - timedelta(days=1)).replace(hour=23, minute=59, second=59, microsecond=999999)
   
    start_time = (today - timedelta(days=1)).replace(hour=23, minute=0, second=0, microsecond=0)
    
    end_time = today.replace(hour=23, minute=59, second=59, microsecond=999999)
    result = md.record_data.query.filter(md.record_data.log_time.between(start_time, end_time)).order_by(md.record_data.log_time).all()
    return jsonify([r.to_dict() for r in result])

@app.route('/api/all_logs')
def get_all_logs():
    result = md.record_data.query.order_by(md.record_data.log_time.desc()).limit(1000).all()
    return jsonify([r.to_dict() for r in result])


@app.route('/api/control', methods=['POST'])
def send_control():
    if control_flag:
        data = request.get_json()
        
        
        if data['device']=='peltier':
            data['device'] = 2
            if data['command'] == '히팅':
                data['command'] = 0
            elif data['command'] == '노말':
                data['command'] = 1
            else:
                data['command'] = 2
                
        
        elif data['device'] == 'door':
            data['device'] = 5
            if data['command'] == 'OPEN':
                data['command'] = 1
            else:
                data['command'] = 0
        else:
            data['device'] = 4
            if data['command'] == 'ON':
                data['command'] = 1
            else:
                data['command'] = 0
                
        print(data['device'])
        print(data['command'])
        
        try:
            
            resp = requests.post(f'{rpi_url}/control', json=data)
            print('RPI 응답:', resp.text)
            # 성공 메시지 리턴
            return jsonify({'msg': 'send success'})
        except Exception as e:
            print(e)
            return jsonify({'msg': 'send error', 'error': str(e)}), 500
    else:
        return jsonify({'msg': 'non active'}), 400
@app.route('/api/control_close')
def stop_control():
    global control_flag
    if control_flag:
        control_flag = False

@app.route('/log')
def log_page():
    return render_template('log.html')

@socketio.on('connect')
def handle_connect():
    logger.info('클라이언트가 연결되었습니다.')
    select_db()

@socketio.on('disconnect')
def handle_disconnect():
    logger.info('클라이언트의 연결이 끊어졌습니다.')

@app.route('/')
def home():
    global sensor_flag
    if not sensor_flag:
        sensor_flag = True
    return render_template('index.html')


    
    

def select_db():
    try:
        last_record = md.db.session.query(md.record_data).order_by(md.record_data.No.desc()).first()
        if last_record:
            data = last_record.to_dict()
            log_time = data.pop('log_time', None)
            if log_time:
                data['timestamp'] = log_time.isoformat()
            socketio.emit('sensor_update', data)
    except Exception as e:
        logger.error("select_db error: %s", e)
    finally:
        md.db.session.remove()

def background_task():
    global sensor_flag
    with app.app_context():
        while True:
            if sensor_flag:
                select_db()

                socketio.sleep(5)
            else:
                socketio.sleep(1)
def reload():
    lastHour = datetime.now().hour
    while True:
        now = datetime.now()
        curHour = now.hour
        if curHour != lastHour:
            socketio.emit('reload_signal')
            lastHour = curHour
        socketio.sleep(10)
        
    

if __name__ == '__main__':
    socketio.start_background_task(background_task)
    socketio.start_background_task(reload)
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, use_reloader=False)