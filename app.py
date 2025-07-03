from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import config

app = Flask(__name__)
app.config.from_object(config)

db = SQLAlchemy(app)

# 예시 모델
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)

    def __repr__(self):
        return f'<User {self.username}>'


def create_tables():
    db.create_all()

# 예시 라우트
@app.route('/')
def index():
    return "Hello, MariaDB with Flask!"

if __name__ == '__main__':
    app.run(debug=True)
