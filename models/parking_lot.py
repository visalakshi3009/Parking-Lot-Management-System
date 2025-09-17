from extensions import db
class ParkingLot(db.Model):
    __tablename__ = 'parking_lot'
    lot_id = db.Column(db.Integer, primary_key = True, autoincrement = True)
    prime_loc_name = db.Column(db.String, nullable = False)
    price = db.Column(db.Numeric, nullable = False)
    address = db.Column(db.String, nullable = False, unique = True)
    pincode = db.Column(db.Integer, nullable = False)
    max_spots = db.Column(db.Integer, nullable = False)
    spots = db.relationship("ParkingSpot", cascade = "all, delete-orphan")