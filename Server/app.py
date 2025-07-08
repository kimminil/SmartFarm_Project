from flask import Flask
from config import SQLALCHEMY_DATABASE_URI, SQLALCHEMY_TRACK_MODIFICATIONS
import models as md
from routes import bp as routes_bp
from collections import deque


que = deque()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = SQLALCHEMY_TRACK_MODIFICATIONS

md.db.init_app(app)
app.register_blueprint(routes_bp)

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
