from time import timezone
import time
from pymongo import ASCENDING
from datetime import datetime
from flask import request, jsonify
import cv2
import re 
import os 
import pytesseract
import warnings
import numpy as np
from dotenv import load_dotenv
from pymongo import MongoClient
from flask import Flask, flash, redirect, render_template, request, url_for 
from PIL import Image

# Load environment variables first
load_dotenv()

# Create the Flask application object
app = Flask(__name__)

# Set the secret key for sessions
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or "a_default_unique_and_secret_key"

warnings.filterwarnings("ignore", message=".*pin_memory.*")

# Database connections
cluster =  MongoClient(os.getenv("MONOGOPASS"))
db = cluster["AestimoData"]
bills_col  = db["expense"]
totals_col = db["total"]
target_col = db["monthlyT"]
target_col.create_index([("key", ASCENDING)], unique=True)


@app.route('/')
def home():
    return render_template('index.html')

@app.route('/bill', methods=['POST'])
def bill():
    file = request.files['file']
    file_bytes = np.frombuffer(file.read(), np.uint8)
    img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    
    img_pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
   
    full_text = pytesseract.image_to_string(img_pil)
    
    lines = full_text.split('\n')
    
    cost = None
    pattern = r"\d{1,3}(?:,\d{3})*(?:\.\d+)?"
    for line in lines:
        if "Total" in line:
            cook = re.search(pattern, line)
            if cook is not None:
                cost = float(cook.group().replace(",", ""))
                break

    if cost is None:
        flash("Couldn't detect a total on that receipt.")
        return redirect(url_for('home'))

    bills_col.insert_one({"cost": cost})
    latest = totals_col.find_one()
    current_total = float(latest.get("total_spent", 0)) if latest else 0.0

    print(current_total)
    print(cost)

    new_total = round(current_total + cost,2)

    totals_col.delete_many({})

    bills_col.insert_one({"cost": cost})
    totals_col.insert_one({"total_spent": new_total})
    return redirect('/stats')


@app.route('/stats')
def stats():
    bill = bills_col.find_one(sort=[("_id", -1)])["cost"]
    total = totals_col.find_one()["total_spent"]
    return render_template('moni.html', price=bill, total=total)

def parse_month(m):
    try:
        return datetime.strptime(m, "%Y-%m")
    except Exception:
        return None

@app.get("/api/targets")
def get_target():
    month = request.args.get("month", "")
    if not parse_month(month):
        return jsonify({"error": "Invalid month. Use YYYY-MM."}), 400
    doc = target_col.find_one({"key": month}, {"_id": 0, "target": 1})
    return jsonify(doc or {}), 200

@app.post("/api/targets")
def upsert_target():
    data = request.get_json(silent=True) or {}
    month, target = data.get("month"), data.get("target")
    dt = parse_month(month)
    if not dt:
        return jsonify({"error": "Invalid month. Use YYYY-MM."}), 400
    try:
        t = float(target)
        if t < 0: raise ValueError
    except Exception:
        return jsonify({"error": "Target must be a non-negative number."}), 400

    target_col.update_one(
        {"key": month},
        {"$set": {
            "key": month, "year": dt.year, "month": dt.month,
            "target": round(t, 2), "updated_at": datetime.utcnow()
        }},
        upsert=True
    )
    time.sleep(2)
    return jsonify({"month": month, "target": round(t, 2)}), 200

@app.delete("/api/targets")
def delete_target():
    month = request.args.get("month", "")
    if not parse_month(month):
        return jsonify({"error": "Invalid month. Use YYYY-MM."}), 400
    target_col.delete_one({"key": month})
    return jsonify({"deleted": month}), 200

@app.route('/info')
def info():
    return render_template('info.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(port=port, debug=False)