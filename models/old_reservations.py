from extensions import db
class OldReservations(db.Model):
    __tablename__ = 'old_reservations'
    __table_args__ = (db.UniqueConstraint('spot_id', 'lot_id', 'parking_timestamp', name = 'old_unique_reservation'),)
    archive_id = db.Column(db.Integer, primary_key = True, autoincrement = True)
    user_id = db.Column(db.Integer, nullable = False)
    spot_id = db.Column(db.Integer, nullable = False)
    lot_id = db.Column(db.Integer, nullable = False)
    vehicle_no = db.Column(db.String, nullable = False)
    parking_timestamp = db.Column(db.DateTime, nullable = False)
    leaving_timestamp = db.Column(db.DateTime)
    archive_time = db.Column(db.DateTime, server_default = db.text('CURRENT_TIMESTAMP'), nullable = False)