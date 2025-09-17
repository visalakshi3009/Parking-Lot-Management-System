from extensions import db
from sqlalchemy import text
from models.parking_lot import ParkingLot
from models.parking_spot import ParkingSpot
from flask import Blueprint, render_template, request, redirect, url_for, session
from flask_login import login_required, current_user
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

admin_bp = Blueprint('admin_bp', __name__)

@admin_bp.route("/admin/dashboard", endpoint = "admin_dashboard")
@login_required
def dashboard():
    error = request.args.get("error")
    spots = db.session.execute(
        text("""
        select *
        from parking_spot natural join parking_lot
        """),
    ).fetchall()
    lots_dict = {}
    for spot in spots:
        if spot.lot_id in lots_dict:
            lots_dict[spot.lot_id]["spots"].append({"spot_id" : spot.spot_id, "status" : spot.status})
        else:
            lots_dict[spot.lot_id] = {"prime_loc_name" : spot.prime_loc_name, "price" : spot.price, "address" : spot.address, "pincode" : spot.pincode, "max_spots" : spot.max_spots, "spots" : []}
            lots_dict[spot.lot_id]["spots"].append({"spot_id" : spot.spot_id, "status" : spot.status})
    return render_template("admin_dashboard.html", name = current_user.name, lots = lots_dict, error = error)

@admin_bp.route("/addlot", methods = ["GET", "POST"])
def addlot():
    if request.method == "POST":
        prime_loc_name = request.form.get("location")
        address = request.form.get("address").strip()
        pincode = int(request.form.get("pincode"))
        price = request.form.get("price")
        maxspots = int(request.form.get("maxspots"))
        if ParkingLot.query.filter_by(address = address).first():
            return render_template("add_lot.html", error = "Parking lot already exists in address!!!")
        new_lot = ParkingLot(prime_loc_name = prime_loc_name, price = price, address = address, pincode = pincode, max_spots = maxspots)
        db.session.add(new_lot)
        db.session.commit()
        lot_id = db.session.execute(
            text("""
            select lot_id
            from parking_lot
            where address = :address
            """),
            {"address" : address}
        ).scalar()
        lastSpot = db.session.execute(
            text("""
            select max(spot_id)
            from parking_spot
            """
            ),
        ).scalar()
        if lastSpot is None:
            lastSpot = 1
        else:
            lastSpot += 1
        for i in range(maxspots):
            new_spot = ParkingSpot(spot_id = lastSpot, lot_id = lot_id, status = 'A')
            db.session.add(new_spot)
            lastSpot += 1
        db.session.commit()
        return render_template("add_lot.html", success = True)
    return render_template("add_lot.html")

@admin_bp.route("/editlot/<int:lot_id>", methods = ["GET", "POST"])
def editlot(lot_id):
    lot = ParkingLot.query.get_or_404(lot_id)
    if request.method == "POST":
        new_address = request.form.get("address").strip()
        new_max_spots = int(request.form.get("maxspots"))
        existing_lot = ParkingLot.query.filter(ParkingLot.address == new_address, ParkingLot.lot_id != lot_id).first()
        if existing_lot:
            return render_template("edit_lot.html", error = "Parking lot already exists in address!!!")
        else:
            lot.prime_loc_name = request.form.get("location")
            lot.address = new_address
            lot.pincode = int(request.form.get("pincode"))
            lot.price = float(request.form.get("price"))
            existing_spots = ParkingSpot.query.filter_by(lot_id = lot_id).count()
            if new_max_spots > existing_spots:
                last_spot_id = db.session.query(db.func.max(ParkingSpot.spot_id)).scalar() or 0
                for _ in range(new_max_spots - existing_spots):
                    last_spot_id += 1
                    db.session.add(ParkingSpot(spot_id = last_spot_id, lot_id = lot_id, status = 'A'))
            elif new_max_spots < existing_spots:
                removable_spots = ParkingSpot.query.filter_by(lot_id = lot_id, status = 'A')\
                                            .order_by(ParkingSpot.spot_id.desc())\
                                            .limit(existing_spots - new_max_spots).all()
                if len(removable_spots) < (existing_spots - new_max_spots):
                    return render_template("edit_lot.html", lot = lot, error = "Cannot reduce spots, some are occupied")
                for spot in removable_spots:
                    db.session.delete(spot)
            lot.max_spots = new_max_spots
            db.session.commit()
            return render_template("edit_lot.html", lot = lot, success = True)
    return render_template("edit_lot.html", lot = lot)

@admin_bp.route("/deletelot/<int:lot_id>")
def deletelot(lot_id):
    occupied_spots = ParkingSpot.query.filter_by(lot_id = lot_id, status = 'O').count()
    if occupied_spots == 0:
        db.session.execute(
            text("""
            delete from parking_lot where lot_id = :lot_id
            """
            ),
            {"lot_id" : lot_id}
        )
        db.session.commit()
        return redirect(url_for("admin_bp.admin_dashboard"))
    return redirect(url_for("admin_bp.admin_dashboard", error = "Cannot Delete Parking Lot, some spots are occupied"))
    

@admin_bp.route("/spot/<int:spot_id>")
def spot(spot_id):
    spot = ParkingSpot.query.filter_by(spot_id = spot_id).first()
    return render_template("spot.html", spot = spot)

@admin_bp.route("/occupied/<int:spot_id>")
def occupied(spot_id):
    user = db.session.execute(
        text("""
        select res_id, user_id, vehicle_no, parking_timestamp, price
        from reserves natural join parking_lot
        where spot_id = :spot_id and leaving_timestamp is null
        order by parking_timestamp desc
        limit 1
        """
        ),
        {"spot_id" : spot_id}
    ).first()
    return render_template("occupied_spot.html", user = user)

@admin_bp.route("/deletespot/<int:spot_id>")
def deletespot(spot_id):
    spot = ParkingSpot.query.filter_by(spot_id = spot_id).first()
    if not spot:
        return redirect(url_for("admin_bp.admin_dashboard", error = "Invalid Parking Spot"))
    if spot.status == 'A':
        lot = ParkingLot.query.filter_by(lot_id = spot.lot_id).first()
        db.session.execute(
            text("""
            delete from parking_spot where spot_id = :spot_id
            """
            ),
            {"spot_id" : spot_id}
        )
        db.session.execute(
            text("""
            update parking_lot set max_spots = :new_spots where lot_id = :lot_id
            """
            ),
            {"new_spots" : lot.max_spots - 1, "lot_id" : lot.lot_id}
        )
        db.session.commit()
        return redirect(url_for("admin_bp.admin_dashboard"))
    return render_template("spot.html", spot = spot, error = "Parking Spot occupied, cannot delete")
    
@admin_bp.route("/displayusers")
def displayusers():
    users = db.session.execute(
        text("""
        select user_id, name, dob, phone_no, email_id
        from user
        where role = "user"
        """
        ),
    ).fetchall()
    return render_template("admin_usersDisp.html", name = current_user.name, users = users)

@admin_bp.route("/searchlots", methods = ["GET", "POST"])
def searchlots():
    loc = None
    data = None
    flag = False
    if request.method == "POST":
        data = request.form.get("searchBar").strip()
        session["data"] = data
        return redirect(url_for("admin_bp.searchlots"))
    if "data" in session:
        flag = True
        data = session.pop("data")
        if data:
            flag = True
            if len(data) == 6 and data.isdigit():
                query = text("""
                    select *
                    from parking_lot natural join parking_spot
                    where pincode = :pin
                    """)
                params = {"pin" : int(data)}
            else:
                query = text("""
                    select *
                    from parking_lot natural join parking_spot
                    where prime_loc_name = :prime
                    """)
                params = {"prime" : data}
            spots = db.session.execute(query, params).fetchall()
            loc = {}
            for spot in spots:
                if spot.lot_id in loc:
                    loc[spot.lot_id]["spots"].append({"spot_id" : spot.spot_id, "status" : spot.status})
                else:
                    loc[spot.lot_id] = {"prime_loc_name" : spot.prime_loc_name, "price" : spot.price, "address" : spot.address, "pincode" : spot.pincode, "max_spots" : spot.max_spots, "spots" : []}
                    loc[spot.lot_id]["spots"].append({"spot_id" : spot.spot_id, "status" : spot.status})
    return render_template("admin_search.html", name = current_user.name, result = loc, prime = data, flag = flag)

@admin_bp.route("/admin/profile", endpoint = "admin_profile")
@login_required
def profile():
    return render_template("admin_profile.html", user = current_user)

@admin_bp.route("/admin/summary", endpoint = "admin_summary")
@login_required
def summary():
    revenue = db.session.execute(
        text("""
        select prime_loc_name, sum(price) as sum
        from parking_lot natural join reserves
        where leaving_timestamp is not null
        group by prime_loc_name
        """
        ),
    ).fetchall()
    plt.figure()
    labels = [lot.prime_loc_name for lot in revenue]
    counts = [lot.sum for lot in revenue]
    plt.bar(labels, counts, color = 'skyblue')
    plt.xlabel("Parking Lots")
    plt.ylabel("Revenue Earned")
    success = False
    if counts:
        success = True
    plt.tight_layout()
    plt.savefig("static/images/admin_summary.png")
    plt.close()
    return render_template("admin_summary.html", name = current_user.name, success = success)