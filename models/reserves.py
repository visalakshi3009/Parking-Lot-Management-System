from extensions import db
class Reserves(db.Model):
    __tablename__ = 'reserves'
    __table_args__ = (db.UniqueConstraint('spot_id', 'lot_id', 'parking_timestamp', name = 'unique_reservation'),
                      db.ForeignKeyConstraint(['spot_id', 'lot_id'], ['parking_spot.spot_id', 'parking_spot.lot_id'], ondelete = 'CASCADE', name = 'fk_pair'))
    res_id = db.Column(db.Integer, primary_key = True, autoincrement = True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id', ondelete = 'CASCADE'), nullable = False)
    spot_id = db.Column(db.Integer, nullable = False)
    lot_id = db.Column(db.Integer, nullable = False)
    vehicle_no = db.Column(db.String, nullable = False)
    parking_timestamp = db.Column(db.DateTime, server_default = db.text('CURRENT_TIMESTAMP'), nullable = False)
    leaving_timestamp = db.Column(db.DateTime)