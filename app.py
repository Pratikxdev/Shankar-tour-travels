"""Shankar Tour & Travels – Flask backend (API + admin panel). Run: python app.py"""
import os, re, json, secrets, threading, urllib.parse, urllib.request, datetime as dt
from functools import wraps
import psycopg2, psycopg2.errors
from psycopg2.extras import RealDictCursor
from werkzeug.exceptions import HTTPException
from werkzeug.security import check_password_hash
from flask import Flask, g, jsonify, request, session, redirect, render_template, send_from_directory
from dotenv import load_dotenv
load_dotenv()   # isi folder me ".env" file hai to usse saari settings yahan load ho jayengi

# ---------- Settings (.env file se, ya seedha environment variable se) ----------
DSN = os.environ.get("DATABASE_URL") or (
    f"host={os.environ.get('DB_HOST','xxxxx')} port={os.environ.get('DB_PORT','xxxxx')} "
    f"dbname={os.environ.get('DB_NAME','xxxxx')} user={os.environ.get('DB_USER','xxxxx')} "
    f"password={os.environ.get('DB_PASSWORD','xxxxx')}")
DEBUG = os.environ.get("DEBUG", "1") == "1"      # hosting ke liye default ab OFF hai; local test karte waqt DEBUG=1 set kar sakte ho
LAYOUTS = {"sedan": ["F1","M1","M2","M3"], "dzire": ["F1","M1","M2","M3"]}
ORIGINS = ["Ballia", "Varanasi", "Lucknow"]
PRICE_KEY = {"F": "front_seat", "M": "middle_seat", "B": "back_seat"}
# WhatsApp notification: WA_MODE = "callmebot" (free, simple) ya "cloud" (official Meta API). Khaali = band.
WA_MODE = os.environ.get("WA_MODE", "").lower()
WA_TO = os.environ.get("WA_TO", "917678891418")          # jis number pe message aana hai (country code ke saath, + ke bina)
CALLMEBOT_KEY = os.environ.get("CALLMEBOT_KEY", "")
WA_TOKEN, WA_PHONE_ID = os.environ.get("WA_TOKEN", ""), os.environ.get("WA_PHONE_ID", "")
ENQ_SERVICES = ["Full Car Booking","Monthly Rental","Wedding Booking","Airport Transfer","One Way Drop","Other"]
# -----------------------------------------------------------------

app = Flask(__name__, static_folder="public/assets", static_url_path="/assets", template_folder="templates")
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-before-going-live")
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax", PERMANENT_SESSION_LIFETIME=dt.timedelta(days=30))

def connect(): return psycopg2.connect(DSN, cursor_factory=RealDictCursor)
def db():
    if "db" not in g: g.db = connect()
    return g.db
@app.teardown_appcontext
def close_db(_):
    c = g.pop("db", None)
    if c: c.close()
def q(sql, args=()):
    with db().cursor() as cur: cur.execute(sql, args); return cur.fetchall()
def one(sql, args=()):
    r = q(sql, args); return r[0] if r else None
def run(sql, args=()):
    with db().cursor() as cur: cur.execute(sql, args)
    db().commit()
def settings(): return {r["key"]: r["value"] for r in q("SELECT key,value FROM settings")}
def route_prices(): return {(r["origin"], r["destination"]): r for r in q("SELECT * FROM route_prices")}
def prices_for(origin, destination, s=None, rp=None):
    """Is route (origin->destination) ke seat prices — agar route_prices me row hai to wahi,
    varna global settings ka default. s/rp pass kar sakte ho agar pehle se load kar rakhe hain."""
    s = s if s is not None else settings()
    rp = rp if rp is not None else route_prices()
    row = rp.get((origin, destination))
    if row: return {"F": row["front_seat"], "M": row["middle_seat"], "B": row["back_seat"]}
    return {"F": int(s["front_seat"]), "M": int(s["middle_seat"]), "B": int(s["back_seat"])}
def err(msg, code=422): return jsonify(error=msg), code
def notify_whatsapp(text):
    """Owner ke WhatsApp pe message bhejta hai. Background me chalta hai, fail hone par booking pe asar nahi padta."""
    if not WA_MODE: return
    def send():
        try:
            if WA_MODE == "callmebot":
                url = "https://api.callmebot.com/whatsapp.php?" + urllib.parse.urlencode({"phone": WA_TO, "text": text, "apikey": CALLMEBOT_KEY})
                urllib.request.urlopen(url, timeout=15).read()
            elif WA_MODE == "cloud":
                req = urllib.request.Request(f"https://graph.facebook.com/v20.0/{WA_PHONE_ID}/messages",
                    data=json.dumps({"messaging_product": "whatsapp", "to": WA_TO, "type": "text", "text": {"body": text}}).encode(),
                    headers={"Authorization": f"Bearer {WA_TOKEN}", "Content-Type": "application/json"})
                urllib.request.urlopen(req, timeout=15).read()
        except Exception:
            app.logger.exception("WhatsApp notification fail hui")
    threading.Thread(target=send, daemon=True).start()

def digits(s): return re.sub(r"\D", "", s or "")[-10:]
def parse_date(s):
    try: return dt.date.fromisoformat(s)
    except (TypeError, ValueError): return None

@app.errorhandler(Exception)
def on_error(e):
    if isinstance(e, HTTPException): return e
    app.logger.exception(e)
    if request.path.startswith("/api/"):
        return err(str(e) if DEBUG else "Server error, thodi der baad try karo.", 500)
    return ("Server error", 500)

@app.get("/")
def index(): return send_from_directory("public", "index.html")

# ---------------- Public API ----------------
@app.get("/api/cars")
def api_cars():
    s = settings()
    cars = q("SELECT id,name,type,plate,driver,ac,blocked_seats FROM cars WHERE active ORDER BY id")
    return jsonify(cars=cars, per_day=int(s["per_day"]), discount=int(s["follow_discount"]),
                   prices={k: int(s[v]) for k, v in PRICE_KEY.items()})

@app.get("/api/seats")
def api_seats():
    d = parse_date(request.args.get("date"))
    origin = request.args.get("origin", "")
    dest = request.args.get("destination", "")
    rows = q("SELECT seat FROM bookings WHERE car_id=%s AND origin=%s AND travel_date=%s AND status<>'Cancelled'",
             (request.args.get("car_id", type=int) or 0, origin, d)) if d else []
    return jsonify(booked=[r["seat"] for r in rows], prices=prices_for(origin, dest))

@app.post("/api/book")
def api_book():
    d = request.get_json(silent=True) or {}
    name, mobile, email = (d.get("name") or "").strip(), digits(d.get("mobile")), (d.get("email") or "").strip()
    seat, origin, dest = d.get("seat") or "", d.get("origin") or "", (d.get("destination") or "").strip()
    date, time = parse_date(d.get("date")), (d.get("time") or "")[:5]
    if not name or len(mobile) != 10: return err("Naam aur 10 digit mobile number sahi daalo.")
    if email and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email): return err("Email sahi nahi hai.")
    if origin not in ORIGINS or not dest or dest == origin: return err("Route sahi chuno.")
    if not date or date < dt.date.today(): return err("Aaj ya aage ki date chuno.")
    car = one("SELECT * FROM cars WHERE id=%s AND active", (int(d.get("car_id") or 0),))
    if not car or seat not in LAYOUTS[car["type"]] or seat in (car["blocked_seats"] or "").split(","):
        return err("Ye seat available nahi hai.")
    s = settings()
    base = prices_for(origin, dest, s=s)[seat[0]]           # route-specific price, server pe calculate hota hai
    discount = 0
    if d.get("follows") and not one("SELECT 1 FROM bookings WHERE mobile=%s AND status<>'Cancelled' LIMIT 1", (mobile,)):
        discount = int(s["follow_discount"])               # sirf pehli booking pe
    total, code = max(0, base - discount), "STT-" + secrets.token_hex(3).upper()
    try:
        run("""INSERT INTO bookings(code,name,mobile,email,car_id,seat,origin,destination,travel_date,travel_time,amount,discount)
               VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (code, name, mobile, email, car["id"], seat, origin, dest, date, time, total, discount))
    except psycopg2.errors.UniqueViolation:
        db().rollback(); return err("Ye seat abhi kisi ne book kar li. Doosri seat chuno.", 409)
    notify_whatsapp(f"*Nayi Booking {code}*\nNaam: {name}\nMobile: {mobile}\nCar: {car['name']} | Seat: {seat}\n"
                    f"Route: {origin} -> {dest}\nDate: {date.strftime('%d/%m/%Y')}\nPickup time customer ko call/WhatsApp karke confirm karo.\n"
                    f"Amount: Rs {total}" + (f" (Rs {discount} off)" if discount else ""))
    return jsonify(code=code, car=car["name"], seat=seat, base=base, discount=discount, total=total)

@app.post("/api/enquiry")
def api_enquiry():
    d = request.get_json(silent=True) or {}
    name, phone = (d.get("name") or "").strip(), digits(d.get("phone"))
    if not name or len(phone) != 10 or d.get("service") not in ENQ_SERVICES: return err("Naam, 10 digit phone aur service chuno.")
    run("INSERT INTO enquiries(service,name,phone,pickup,drop_or_venue,travel_date,travel_time,details) VALUES(%s,%s,%s,%s,%s,%s,%s,%s)",
        (d["service"], name, phone, (d.get("pickup") or "")[:120], (d.get("drop") or "")[:120],
         parse_date(d.get("date")), (d.get("time") or "")[:5], (d.get("details") or "")[:500]))
    notify_whatsapp(f"*Nayi Enquiry: {d['service']}*\nNaam: {name}\nPhone: {phone}\nPickup: {d.get('pickup') or '-'}\n"
                    f"Drop/Venue: {d.get('drop') or '-'}\nDate: {d.get('date') or '-'} {d.get('time') or ''}\n{(d.get('details') or '')[:200]}")
    return jsonify(ok=True)

@app.get("/api/reviews")
def api_reviews():
    return jsonify(reviews=q("SELECT name,rating,comment,created_at FROM reviews WHERE approved ORDER BY created_at DESC LIMIT 50"))

@app.post("/api/review")
def api_review_submit():
    d = request.get_json(silent=True) or {}
    name, rating, comment = (d.get("name") or "").strip()[:60], d.get("rating"), (d.get("comment") or "").strip()[:500]
    if not name or rating not in (1, 2, 3, 4, 5) or not comment: return err("Naam, rating (1-5 star) aur chhota sa comment daalo.")
    run("INSERT INTO reviews(name,rating,comment) VALUES(%s,%s,%s)", (name, rating, comment))
    notify_whatsapp(f"*Naya Review* ({rating}★)\n{name}: {comment}\nDashboard se approve karo tabhi website par dikhega.")
    return jsonify(ok=True)

# ---------------- Admin ----------------
def admin_only(f):
    @wraps(f)
    def w(*a, **k):
        return f(*a, **k) if session.get("admin") else redirect("/admin/login")
    return w

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    msg = ""
    if request.method == "POST":
        try:
            a = one("SELECT * FROM admins WHERE username=%s", (request.form.get("username", "").strip(),))
            if a and check_password_hash(a["password_hash"], request.form.get("password", "")):
                session.clear(); session["admin"] = a["username"]; session["csrf"] = secrets.token_hex(16)
                session.permanent = bool(request.form.get("remember"))   # ticked = 30 din yaad rakhega, varna browser band hote hi logout
                return redirect("/admin")
            msg = "Username ya password galat hai."
        except psycopg2.Error as e:
            app.logger.exception(e); msg = str(e) if DEBUG else "Database connection failed"
    return render_template("login.html", msg=msg)

@app.get("/admin/logout")
def admin_logout(): session.clear(); return redirect("/admin/login")

@app.route("/admin", methods=["GET", "POST"])
@admin_only
def admin_dashboard():
    if request.method == "POST":
        f = request.form
        if not secrets.compare_digest(session.get("csrf", ""), f.get("csrf", "")): return "Invalid request", 400
        a = f.get("action")
        if a == "status" and f.get("status") in ("Pending", "Confirmed", "Cancelled"):
            run("UPDATE bookings SET status=%s WHERE id=%s", (f["status"], f.get("id", type=int)))
        elif a == "prices":
            for k in ("front_seat", "middle_seat", "back_seat", "per_day", "follow_discount"):
                run("UPDATE settings SET value=%s WHERE key=%s", (str(max(0, f.get(k, 0, type=int))), k))
        elif a == "car_toggle":
            car = one("SELECT type, active FROM cars WHERE id=%s", (f.get("id", type=int),))
            if car and (car["active"] or car["type"] in LAYOUTS):   # disable hamesha allowed; enable sirf supported type ke liye
                run("UPDATE cars SET active = NOT active WHERE id=%s", (f.get("id", type=int),))
        elif a == "car_add" and f.get("type") in LAYOUTS and f.get("name", "").strip():
            run("INSERT INTO cars(name,type,plate,driver) VALUES(%s,%s,%s,%s)", (f["name"].strip(), f["type"], f.get("plate", "").strip(), f.get("driver", "").strip()))
        elif a == "car_blocked":
            run("UPDATE cars SET blocked_seats=%s WHERE id=%s", (re.sub(r"[^A-Z0-9,]", "", f.get("blocked", "").upper()), f.get("id", type=int)))
        elif a == "route_price" and f.get("origin") in ORIGINS and f.get("destination", "").strip():
            run("""INSERT INTO route_prices(origin,destination,front_seat,middle_seat,back_seat) VALUES(%s,%s,%s,%s,%s)
                   ON CONFLICT (origin,destination) DO UPDATE SET front_seat=EXCLUDED.front_seat,
                   middle_seat=EXCLUDED.middle_seat, back_seat=EXCLUDED.back_seat""",
                (f["origin"], f["destination"].strip(), max(0, f.get("front_seat", 0, type=int)),
                 max(0, f.get("middle_seat", 0, type=int)), max(0, f.get("back_seat", 0, type=int))))
        elif a == "route_price_delete":
            run("DELETE FROM route_prices WHERE origin=%s AND destination=%s", (f.get("origin", ""), f.get("destination", "")))
        elif a == "review_approve": run("UPDATE reviews SET approved=TRUE WHERE id=%s", (f.get("id", type=int),))
        elif a == "review_delete": run("DELETE FROM reviews WHERE id=%s", (f.get("id", type=int),))
        return redirect("/admin")
    n = lambda sql: one(sql)["n"]
    stats = [("Total bookings", n("SELECT count(*) n FROM bookings")), ("Today's bookings", n("SELECT count(*) n FROM bookings WHERE created_at::date=current_date")),
             ("Pending", n("SELECT count(*) n FROM bookings WHERE status='Pending'")), ("Active cars", n("SELECT count(*) n FROM cars WHERE active")),
             ("Revenue (Confirmed)", "₹{:,}".format(n("SELECT coalesce(sum(amount),0) n FROM bookings WHERE status='Confirmed'")))]
    return render_template("dashboard.html", user=session["admin"], csrf=session["csrf"], stats=stats, s=settings(),
        bookings=q("SELECT b.*, c.name car FROM bookings b JOIN cars c ON c.id=b.car_id ORDER BY b.id DESC LIMIT 100"),
        cars=q("SELECT * FROM cars ORDER BY id"), enquiries=q("SELECT * FROM enquiries ORDER BY id DESC LIMIT 30"), types=list(LAYOUTS),
        route_prices=q("SELECT * FROM route_prices ORDER BY origin, destination"), origins=ORIGINS,
        reviews=q("SELECT * FROM reviews ORDER BY approved, created_at DESC"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)), debug=DEBUG)
