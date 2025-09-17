from extensions import db
class ParkingSpot(db.Model):
    __tablename__ = 'parking_spot'
    __table_args__ = (db.CheckConstraint("status in ('A', 'O')", name = 'check_status'),)
    spot_id = db.Column(db.Integer, primary_key = True, unique = True)
    lot_id = db.Column(db.Integer, db.ForeignKey('parking_lot.lot_id', ondelete = 'CASCADE'), primary_key = True)
    status = db.Column(db.CHAR(1), nullable = False)