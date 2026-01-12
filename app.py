from flask import Flask, request, Response, render_template
from flask_cors import CORS
import requests
import concurrent.futures
import os
from dotenv import load_dotenv

# 🔹 LOAD ENV VARIABLES
load_dotenv()

app = Flask(__name__)
CORS(app)

# 🔹 STUDENT LIST
students = [
    {
        "username": "e22cseu0519@bennett.edu.in",
        "password": os.getenv("JATIN_PASS"),
        "name": "Jatin"
    },
    {
        "username": "e22cseu0537@bennett.edu.in",
        "password": os.getenv("SHREYA_PASS"),
        "name": "Shreya"
    }
]

def login(username, password):
    response = requests.post(
        "https://student.bennetterp.camu.in/login/validate",
        json={
            "dtype": "M",
            "Email": username,
            "pwd": password
        },
        timeout=10
    )

    data = response.json()["output"]["data"]["logindetails"]["Student"][0]
    stu_id = data["StuID"]
    cookie = response.headers["Set-Cookie"].split(";")[0].split("=")[1]
    return stu_id, cookie

def mark(stu_id, cookie, qr):
    response = requests.post(
        "https://student.bennetterp.camu.in/api/Attendance/record-online-attendance",
        cookies={"connect.sid": cookie},
        json={
            "attendanceId": qr,
            "StuID": stu_id,
            "offQrCdEnbld": True
        },
        timeout=10
    )
    return response.json()["output"]["data"]["code"]

def worker(student, qr):
    try:
        if not student["password"]:
            return f"{student['name']}: PASSWORD NOT SET\n"

        stu_id, cookie = login(student["username"], student["password"])
        result = mark(stu_id, cookie, qr)
        return f"{student['name']}: {result}\n"

    except Exception as e:
        print(f"[ERROR] {student['name']} → {e}")
        return f"{student['name']}: ERROR\n"

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/scan", methods=["POST"])
def scan():
    qr = request.json["qr"]

    def stream():
        with concurrent.futures.ThreadPoolExecutor() as exe:
            futures = [exe.submit(worker, s, qr) for s in students]
            for f in concurrent.futures.as_completed(futures):
                yield f.result()

    return Response(stream(), content_type="text/plain")

# 🔹 FOR RENDER / GUNICORN
if __name__ != "__main__":
    application = app
