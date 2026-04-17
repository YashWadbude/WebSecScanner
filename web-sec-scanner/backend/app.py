# (Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned) ; (& c:\Project\web-sec-scanner\.venv\Scripts\Activate.ps1)
# PS C:\Project\web-sec-scanner> pip install flask requests beautifulsoup4
# PS C:\Project\web-sec-scanner> c:\Project\web-sec-scanner\.venv\Scripts\python.exe -m pip install flask requests beautifulsoup4
# PS C:\Project\web-sec-scanner> pip install flask requests beautifulsoup4


# backend 
# cd backend 
# (.venv) PS C:\Project\web-sec-scanner\backend> python app.py

# frontend 
# cd frontend 
# (.venv) PS C:\Project\web-sec-scanner\frontend> python -m http.server 5500



from flask import Flask, request, Response, jsonify
from flask_cors import CORS
import json
import time
import datetime
import jwt

from scanner.crawler import crawl_website
from scanner.xss import scan_xss
from scanner.sqli import scan_sqli
from scanner.headers import scan_headers
from scanner.utils import scan_directories

from database.db import get_db, init_db

app = Flask(__name__)
CORS(app)

SECRET_KEY = "my_super_secure_secret_key_1234567890_abcdef"

init_db()


# =========================
# 🔐 AUTH HELPERS
# =========================
def generate_token(user_id, username):
    return jwt.encode({
        "user_id": user_id,
        "username": username,
        "exp": datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=2)
    }, SECRET_KEY, algorithm="HS256")


def verify_token(token):
    try:
        data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return data
    except Exception as e:
        print("❌ TOKEN ERROR:", e)
        return None


# =========================
# 🔐 SIGNUP
# =========================
@app.route("/signup", methods=["POST"])
def signup():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    db = get_db()

    try:
        db.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, password)
        )
        db.commit()
        return jsonify({"message": "User created"})
    except:
        return jsonify({"error": "Username already exists"}), 400


# =========================
# 🔐 LOGIN
# =========================
@app.route("/login", methods=["POST"])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    db = get_db()

    user = db.execute(
        "SELECT id, username FROM users WHERE username=? AND password=?",
        (username, password)
    ).fetchone()

    if user:
        token = generate_token(user["id"], user["username"])
        return jsonify({"token": token})
    else:
        return jsonify({"error": "Invalid credentials"}), 401


# =========================
# 🔐 PROFILE
# =========================
@app.route("/profile", methods=["GET"])
def profile():
    token = request.headers.get("Authorization")

    if not token:
        return jsonify({"error": "No token"}), 401

    data = verify_token(token)

    if not data:
        return jsonify({"error": "Invalid token"}), 401

    return jsonify({
        "user_id": data["user_id"],
        "username": data["username"]
    })


# =========================
# 💾 SAVE SCAN
# =========================
def save_scan(user_id, url, results):
    db = get_db()
    db.execute(
        "INSERT INTO scans (user_id, target, results, date) VALUES (?, ?, ?, ?)",
        (user_id, url, json.dumps(results), str(datetime.datetime.now()))
    )
    db.commit()


# =========================
# 🔥 SCAN ENGINE
# =========================
def generate_scan(url, user_id):
    results = []

    yield f"data: {json.dumps({'progress': 10, 'log': 'Connecting...'})}\n\n"
    time.sleep(1)

    links = crawl_website(url)

    for link in links:
        yield f"data: {json.dumps({'progress': 50, 'log': f'Scanning {link}'})}\n\n"

        results += scan_xss(link)
        results += scan_sqli(link)
        results += scan_headers(link)

    results += scan_directories(url)

    save_scan(user_id, url, results)

    yield f"data: {json.dumps({'progress': 100, 'done': True})}\n\n"


# =========================
# 🔥 SCAN ROUTE
# =========================
@app.route("/scan-stream")
def scan_stream():
    url = request.args.get("url")
    token = request.args.get("token")

    if not token:
        return "Unauthorized", 401

    data = verify_token(token)

    if not data:
        return "Invalid token", 401

    return Response(
        generate_scan(url, data["user_id"]),
        mimetype="text/event-stream"
    )


# =========================
# 🔥 FETCH USER SCANS
# =========================
@app.route("/my-scans", methods=["GET"])
def my_scans():
    token = request.headers.get("Authorization")

    if not token:
        return jsonify({"error": "No token"}), 401

    data = verify_token(token)

    if not data:
        return jsonify({"error": "Invalid token"}), 401

    db = get_db()

    scans = db.execute(
        "SELECT target, results, date FROM scans WHERE user_id=? ORDER BY id DESC",
        (data["user_id"],)
    ).fetchall()

    result = []

    for scan in scans:
        result.append({
            "target": scan["target"],
            "results": json.loads(scan["results"]),
            "date": scan["date"]
        })

    return jsonify(result)


@app.route("/")
def home():
    return "Backend Running"


if __name__ == "__main__":
    app.run(debug=True)