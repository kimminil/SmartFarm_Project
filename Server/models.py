
from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()

class testData(db.Model):
    __tablename__ = 'test_table'
    
    id = db.Column(db.Integer,primary_key=True,index=True)
    temp = db.Column(db.Float,index=True)
    humi = db.Column(db.Float,index=True)
    co2 = db.Column(db.Float,index=True)
    light = db.Column(db.Float,index=True)
    cmd_temp = db.Column(db.String(20))
    cmd_humi = db.Column(db.String(20))
    cmd_co2 = db.Column(db.String(20))
    cmd_light = db.Column(db.String(20))
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
    cmd_temp_peltier = db.Column(db.VARCHAR(50),index=True)
    cmd_fan = db.Column(db.VARCHAR(10),index=True)
    cmd_light = db.Column(db.VARCHAR(10),index=True)
    cmd_co2_vent = db.Column(db.VARCHAR(10),index=True)
    
    def to_dict(self):
       return { c.name: getattr(self, c.name) 
                for c in self.__table__.columns }

class record_product_condition(db.Model):
    __tablename__='record_product_condition'
    no = db.Column(db.Integer,primary_key=True,index=True)
    pos1 = db.Column(db.VARCHAR(10),index=True)
    pos2 = db.Column(db.VARCHAR(10),index=True)
    pos3 = db.Column(db.VARCHAR(10),index=True)
    pos4 = db.Column(db.VARCHAR(10),index=True)

    status = db.Column(db.VARCHAR(10),index=True)
    
    @classmethod
    def update_data(cls,db_session,data_dict):        
        entry = db_session.query(cls).get(1)
        if entry:
            for k,v in data_dict.items():
               if hasattr(entry,k):
                   setattr(entry,k,v)
            db_session.commit()
            return True
        return False