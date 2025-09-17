import os
from extensions import db, login_manager
from flask import Flask
from models.user import User
from routes.admin_route import admin_bp
from routes.user_routes import user_bp
from flask import render_template, request, redirect, url_for
from flask_login import login_user, login_required, logout_user
from werkzeug.security import check_password_hash
from sqlalchemy import event
from sqlalchemy.engine import Engine
import sqlite3

cur_dir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///" + os.path.join(cur_dir, "instance/database.sqlite3")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "fallback_key")

db.init_app(app)

@event.listens_for(Engine, "connect")
def enable_foreign_keys(dbapi_connection, connection_record):
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.close()

app.app_context().push()

login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

app.register_blueprint(admin_bp)
app.register_blueprint(user_bp)

@app.route("/", methods = ["GET", "POST"])
def login():
    success = request.args.get("success")
    if request.method == "POST":
        email_id = request.form.get("email")
        password = request.form.get("password")
        role = request.form.get("user_type").lower()
        user = User.query.filter_by(email_id = email_id).first()
        if user and check_password_hash(user.password, password):
            if user.role == role:
                login_user(user)
                if user.role == 'user':
                    return redirect(url_for("user_bp.user_dashboard"))
                return redirect(url_for("admin_bp.admin_dashboard"))
            else:
                return render_template("login_page.html", error = "Incorrect role chosen")
        else:
            return render_template("login_page.html", error = "Invalid Email ID or Password !!")
    return render_template("login_page.html", success = success)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug = True)