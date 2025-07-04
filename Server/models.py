from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class testData(db.Model):
    __tablename__ = 'test_table'
    
    id = db.Column(db.Integer,primary_key=True,index=True)
    email = db.Column(db.VARCHAR(64), index=True)
    pwd = db.Column(db.VARCHAR(64), index=True)