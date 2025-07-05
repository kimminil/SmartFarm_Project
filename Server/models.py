
from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()

class testData(db.Model):
    __tablename__ = 'test_table'
    
    id = db.Column(db.Integer,primary_key=True,index=True)
    temp = db.Column(db.Float,index=True)

class record_control_condition(db.Model):
    __tablename__ = 'record_control_condition'
    product_num = db.Column(db.Integer,primary_key=True,index=True)
    temp_min = db.Column(db.Float,index=True)
    temp_max = db.Column(db.Float,index=True)
    humi_min = db.Column(db.Float,index=True)
    humi_max = db.Column(db.Float,index=True)
    co2_min = db.Column(db.Float,index=True)
    co2_max = db.Column(db.Float,index=True)
    light_min = db.Column(db.Float,index=True)
    light_max = db.Column(db.Float,index=True)
    w_height_min = db.Column(db.Float,index=True)
    w_height_max = db.Column(db.Float,index=True)

class record_access(db.Model):
    __tablename__='record_access'
    No = db.Column(db.Integer,primary_key=True,index=True)
    access_time = db.Column(db.DateTime,index=True)

class record_data(db.Model):
    __tablename__ = 'record_data'
    No = db.Column(db.Integer,primary_key=True,index=True)
    log_time = db.Column(db.DateTime,index=True)
    temp = db.Column(db.Float,index=True)
    humi = db.Column(db.Float,index=True)
    co2 = db.Column(db.Float,index=True)
    light= db.Column(db.Float,index=True)
    w_height = db.Column(db.Float,index=True)
    cmd_Peltier = db.Column(db.VARCHAR(50),index=True)
    cmd_fan = db.Column(db.VARCHAR(10),index=True)
    cmd_light = db.Column(db.VARCHAR(10),index=True)
    cmd_w_pump = db.Column(db.VARCHAR(10),index=True)

class record_product_condition(db.Model):
    __tablename__='record_product_condition'
    product_posi = db.Column(db.VARCHAR(10),primary_key=True,index=True)
    status = db.Column(db.VARCHAR(10),index=True)