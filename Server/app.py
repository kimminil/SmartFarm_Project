from flask import Flask, request, jsonify,render_template
from flask_socketio import SocketIO
from config import SQLALCHEMY_DATABASE_URI, SQLALCHEMY_TRACK_MODIFICATIONS
import models as md
from routes import bp as routes_bp
import os
import logging
from datetime import datetime, timedelta
from logging.handlers import RotatingFileHandler
UPLOAD_FOLDER="./image"
os.makedirs(UPLOAD_FOLDER,exist_ok=True)


def select_db():
    md.db.session.remove()
    last_record = (
        md.record_data.query
        .order_by(md.record_data.No.desc())
        .first())
    if last_record:
        data = last_record.to_dict()
        data['timestamp'] = data['log_time'].isoformat()
        del data['log_time']
        socketio.emit('sensor_update',
                      data,
                      )
    

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



@app.route('/upload', methods=['POST'])
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
            socketio.sleep(60)

if __name__ == '__main__':
    socketio.start_background_task(background_task)
    
    socketio.run(app,
                 host='0.0.0.0',
                 port=5000,
                 debug=True,
                 use_reloader=False)  # 리로더 끄기
