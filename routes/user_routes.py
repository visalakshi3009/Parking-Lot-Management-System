from extensions import db
from sqlalchemy import text
from flask import Blueprint, render_template, request, redirect, url_for, session
from models.user import User
from models.parking_lot import ParkingLot
from models.parking_spot import ParkingSpot
from models.reserves import Reserves
from routes.admin_route import admin_bp
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from datetime import datetime
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

user_bp = Blueprint('user_bp', __name__)

@user_bp.route("/register", methods = ["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name")
        dob_str = request.form.get("dob")
        dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
        phone_no = request.form.get("phone")
        email_id = request.form.get("email")
        password = request.form.get("password")
        if User.query.filter_by(email_id = email_id).first():
            return render_template("register.html", error = "Email ID already in use, cannot register !!")
        if User.query.filter_by(phone_no = phone_no).first():
            return render_template("register.html", error = "Phone Number already in use, cannot register !!")
        hashed_password = generate_password_hash(password, method = "pbkdf2:sha256")
        new_user = User(name = name, dob = dob, phone_no = phone_no, email_id = email_id, password = hashed_password, role = "user")
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for("login", success = True))
    return render_template("register.html")

@user_bp.route("/user/dashboard", endpoint = "user_dashboard", methods = ["GET", "POST"])
@login_required
def dashboard():
    par_his = db.session.execute(
        text("""
        select res_id, prime_loc_name, vehicle_no, parking_timestamp, status, leaving_timestamp
        from reserves natural join parking_lot natural join parking_spot
        where user_id = :uid
        order by parking_timestamp desc
        limit 3
        """),
        {"uid" : current_user.user_id}
    ).fetchall()
    loc = None
    data = None
    flag = False
    if request.method == "POST":
        data = request.form.get("searchBar").strip()
        session["data"] = data
        return redirect(url_for("user_bp.user_dashboard"))
    if "data" in session:
        flag = True
        data = session.pop("data")
        if data:
            flag = True
            if len(data) == 6 and data.isdigit():
                query = text("""
                    select lot_id, address, count(*) as spots
                    from parking_lot natural join parking_spot
                    where pincode = :pin and status = 'A'
                    group by lot_id, address 
                    order by lot_id
                    """)
                params = {"pin" : int(data)}
            else:
                query = text("""
                    select lot_id, address, count(*) as spots
                    from parking_lot natural join parking_spot
                    where prime_loc_name = :prime and status = 'A'
                    group by lot_id, address 
                    order by lot_id
                    """)
                params = {"prime" : data}
            loc = db.session.execute(query, params).fetchall()
    return render_template("dashboard.html", name = current_user.name, history = par_his, result = loc, prime = data, flag = flag)

@user_bp.route("/bookspot/<int:lot_id>", methods = ["GET", "POST"])
def bookspot(lot_id):
    if request.method == "POST":
        user_id = request.form.get("user_id")
        spot_id = request.form.get("spot_id")
        vehicle_no = request.form.get("vehicle")
        spot = ParkingSpot.query.filter_by(spot_id = spot_id, lot_id = lot_id).first()
        if not spot or spot.status == 'O':
            return render_template("reservation.html", error = "No Spots Available", user = current_user)
        current = datetime.now()
        reservation = Reserves(user_id = user_id, spot_id = spot_id, lot_id = lot_id, vehicle_no = vehicle_no, parking_timestamp = current)
        db.session.add(reservation)
        spot.status = 'O'
        db.session.commit()
        return render_template("reservation.html", spot = spot, user = current_user, success = True)
    spot = ParkingSpot.query.filter_by(lot_id = lot_id, status = 'A').first()
    if not spot:
        return render_template("reservation.html", error = "No Spots Available", user = current_user)
    return render_template("reservation.html", spot = spot, user = current_user)

@user_bp.route("/releasespot/<int:res_id>", methods = ["GET", "POST"])
def releasespot(res_id):
    reservation = Reserves.query.get_or_404(res_id)
    spot_id = reservation.spot_id
    current = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cost = db.session.execute(
        text("""
        select price
        from parking_lot natural join parking_spot
        where spot_id = :spot_id
        """),
        {"spot_id" : spot_id}
    ).scalar()
    if request.method == "POST":
        leaving_time = request.form.get("leaving_time")
        db.session.execute(
            text("""
            update reserves set leaving_timestamp = :leaving_time where res_id = :res_id
            """
            ),
            {"leaving_time" : leaving_time, "res_id" : res_id}
        )
        db.session.execute(
            text("""
            update parking_spot set status = 'A' where spot_id = :spot_id
            """
            ),
            {"spot_id" : spot_id}
        )
        db.session.commit()
        return render_template("release_spot.html", reservation = reservation, cost = cost, success = True)
    return render_template("release_spot.html", reservation = reservation, cost = cost, current_timestamp = current)

@user_bp.route("/user/profile", endpoint = "user_profile")
@login_required
def profile():
    return render_template("user_profile.html", user = current_user)

@user_bp.route("/deleteuser", methods = ["POST"])
@login_required
def deleteuser():
    count = db.session.execute(
        text("""
        select count(*)
        from reserves
        where user_id = :u_id and leaving_timestamp is null
        """
        ),
        {"u_id" : current_user.user_id}
    ).scalar()
    if count == 0:
        db.session.execute(
            text("""
            delete from user where user_id = :u_id
            """
            ),
            {"u_id" : current_user.user_id}
        )
        db.session.commit()
        return redirect(url_for("login"))
    return render_template("user_profile.html", user = current_user, error = "Parking spots currently occupied, cannot delete account")

@user_bp.route("/user/summary", endpoint = "user_summary")
@login_required
def summary():
    summ = db.session.execute(
        text("""
        select prime_loc_name, count(*) as count
        from reserves natural join parking_lot
        where user_id = :u_id
        group by prime_loc_name
        """),
        {"u_id" : current_user.user_id}
    ).fetchall()
    plt.figure()
    labels = [lot.prime_loc_name for lot in summ]
    counts = [lot.count for lot in summ]
    plt.bar(labels, counts, color = 'skyblue')
    plt.xlabel("Parking Lots")
    plt.ylabel("Reservations Made")
    if counts:
        plt.yticks(range(0, max(counts) + 1))
    plt.tight_layout()
    plt.savefig("static/images/user_summary.png")
    plt.close()
    return render_template("user_summary.html", summary = summ, name = current_user.name)