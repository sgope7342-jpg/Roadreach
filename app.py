import os, sqlite3, re
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, send_file, abort
from io import BytesIO
import qrcode

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-before-production")
DB_PATH = os.environ.get("DATABASE_PATH", "roadreach.db")

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with db() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS vehicles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            serial TEXT UNIQUE NOT NULL,
            owner_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            vehicle_type TEXT NOT NULL,
            plate_hint TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS help_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_type TEXT NOT NULL,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            location TEXT NOT NULL,
            details TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")

def next_serial(conn):
    row = conn.execute("SELECT COALESCE(MAX(id), 0) + 1 AS n FROM vehicles").fetchone()
    return f"RR-JSR-{int(row['n']):04d}"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("owner_name", "").strip()
        phone = re.sub(r"\D", "", request.form.get("phone", ""))
        vehicle_type = request.form.get("vehicle_type", "Car").strip()
        plate_hint = request.form.get("plate_hint", "").strip()
        if not name or len(phone) != 10:
            flash("Owner name aur valid 10-digit mobile number enter karein.", "error")
            return render_template("register.html")
        with db() as conn:
            serial = next_serial(conn)
            conn.execute("INSERT INTO vehicles(serial, owner_name, phone, vehicle_type, plate_hint) VALUES(?,?,?,?,?)",
                         (serial, name, phone, vehicle_type, plate_hint))
        return redirect(url_for("vehicle_card", serial=serial))
    return render_template("register.html")

@app.route("/v/<serial>")
def vehicle_card(serial):
    with db() as conn:
        vehicle = conn.execute("SELECT serial, vehicle_type, plate_hint FROM vehicles WHERE serial=?", (serial.upper(),)).fetchone()
    if not vehicle:
        abort(404)
    return render_template("vehicle.html", vehicle=vehicle)

@app.route("/qr/<serial>.png")
def qr_png(serial):
    target = request.url_root.rstrip("/") + url_for("contact_lookup")
    img = qrcode.make(target)
    bio = BytesIO()
    img.save(bio, format="PNG")
    bio.seek(0)
    return send_file(bio, mimetype="image/png", download_name=f"{serial}.png")

@app.route("/contact", methods=["GET", "POST"])
def contact_lookup():
    vehicle = None
    if request.method == "POST":
        serial = request.form.get("serial", "").strip().upper()
        with db() as conn:
            vehicle = conn.execute("SELECT serial, owner_name, phone, vehicle_type, plate_hint FROM vehicles WHERE serial=?", (serial,)).fetchone()
        if not vehicle:
            flash("Serial number nahi mila. QR card par diya number dobara check karein.", "error")
    return render_template("contact.html", vehicle=vehicle)

@app.route("/api/lookup", methods=["POST"])
def api_lookup():
    data = request.get_json(silent=True) or {}
    serial = str(data.get("serial", "")).strip().upper()
    if not re.fullmatch(r"RR-JSR-\d{4,}", serial):
        return jsonify({"ok": False, "message": "Valid serial number enter karein."}), 400
    with db() as conn:
        vehicle = conn.execute("SELECT serial, owner_name, phone, vehicle_type, plate_hint FROM vehicles WHERE serial=?", (serial,)).fetchone()
    if not vehicle:
        return jsonify({"ok": False, "message": "Serial number nahi mila."}), 404
    return jsonify({"ok": True, "serial": vehicle["serial"], "owner_name": vehicle["owner_name"],
                    "phone": vehicle["phone"], "vehicle_type": vehicle["vehicle_type"], "plate_hint": vehicle["plate_hint"]})

@app.route("/help", methods=["GET", "POST"])
def roadside_help():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        phone = re.sub(r"\D", "", request.form.get("phone", ""))
        location = request.form.get("location", "").strip()
        help_type = request.form.get("help_type", "Mechanic").strip()
        details = request.form.get("details", "").strip()
        if not name or len(phone) != 10 or not location:
            flash("Name, valid 10-digit mobile number aur location zaroori hain.", "error")
            return render_template("help.html")
        with db() as conn:
            conn.execute("INSERT INTO help_requests(request_type, name, phone, location, details) VALUES(?,?,?,?,?)",
                         (help_type, name, phone, location, details))
        return render_template("help.html", submitted=True)
    return render_template("help.html", submitted=False)

@app.route("/sos", methods=["GET", "POST"])
def sos():
    if request.method == "POST":
        name = request.form.get("name", "").strip() or "Not provided"
        phone = re.sub(r"\D", "", request.form.get("phone", ""))
        location = request.form.get("location", "").strip()
        details = request.form.get("details", "").strip()
        if not location:
            flash("Apni current location ya nearby landmark enter karein.", "error")
            return render_template("sos.html")
        with db() as conn:
            conn.execute("INSERT INTO help_requests(request_type, name, phone, location, details) VALUES(?,?,?,?,?)",
                         ("SOS request (website log only)", name, phone, location, details))
        return render_template("sos.html", submitted=True)
    return render_template("sos.html", submitted=False)

@app.errorhandler(404)
def not_found(_):
    return render_template("404.html"), 404

init_db()
if __name__ == "__main__":
    app.run(debug=True)