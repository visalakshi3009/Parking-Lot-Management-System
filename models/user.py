from extensions import db
from flask_login import UserMixin
class User(UserMixin, db.Model):
    __tablename__ = 'user'
    __table_args__ = (db.CheckConstraint("role in ('user', 'admin')", name = 'check_role'),)
    user_id = db.Column(db.Integer, primary_key = True, autoincrement = True)
    name = db.Column(db.String, nullable = False)
    dob = db.Column(db.Date, nullable = False)
    phone_no = db.Column(db.Numeric, nullable = False, unique = True)
    email_id = db.Column(db.String, nullable = False, unique = True)
    password = db.Column(db.String, nullable = False)
    role = db.Column(db.String, nullable = False)
    def get_id(self):
        return str(self.user_id)