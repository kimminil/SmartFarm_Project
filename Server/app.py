from flask import Flask, request, jsonify
from config import SQLALCHEMY_DATABASE_URI, SQLALCHEMY_TRACK_MODIFICATIONS
import models as md
from routes import bp as routes_bp
from collections import deque
import os

UPLOAD_FOLDER="./image"
os.makedirs(UPLOAD_FOLDER,exist_ok=True)


que = deque()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = SQLALCHEMY_TRACK_MODIFICATIONS
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

md.db.init_app(app)
app.register_blueprint(routes_bp)

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


@app.route('/')
def home():
    '''
    rows = (
        testData.query
        .with_entities(testData.email,testData.id)
        .order_by(testData.id)
        .all()
            
    )
    emails = [e for e,_ in rows]
    result=""
    for r in emails:
        que.append(r)
    for r in que:
        result += str(r)
        result += " "
    return result
'''
    return "test"

if __name__ == '__main__':
    app.run(host='0.0.0.0',debug=True, port=5000)
