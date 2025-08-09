from time import timezone
import time
from pymongo import ASCENDING
from datetime import datetime
from flask import request, jsonify
import cv2
import re 
import os 
import easyocr
import warnings
import numpy as np
from dotenv import load_dotenv
from pymongo import MongoClient
from flask import Flask, flash, redirect, render_template, request, url_for 

app = Flask(__name__)

load_dotenv()

warnings.filterwarnings("ignore", message=".*pin_memory.*")

cluster =  MongoClient(os.getenv("MONOGOPASS"))
db = cluster["AestimoData"]
bills_col  = db["expense"]   # individual bills
totals_col = db["total"]
target_col = db["monthlyT"]  # target expenses 
target_col.create_index([("key", ASCENDING)], unique=True)


reader = easyocr.Reader(['en'])

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/bill', methods=['POST'])
def bill():
    file = request.files['file']
    file_bytes = np.frombuffer(file.read(), np.uint8)
    img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
   
    result = reader.readtext(img)
    money_yes = False
    cost = None
    #Print the extracted text
    pattern = r"\d{1,3}(?:,\d{3})*(?:\.\d+)?"
    for detection in result:
        if money_yes:
            cook = re.search(pattern, detection[1])
            if cook is not None:
                cost = float(cook.group().replace(",", ""))
                money_yes = False
        if "Total"  in detection[1]:
            money_yes = True

    if cost is None:
        flash("Couldn't detect a total on that receipt.")
        return redirect(url_for('home'))

    # Get current total
    bills_col.insert_one({"cost": cost})
    latest = totals_col.find_one()
    current_total = float(latest.get("total_spent", 0)) if latest else 0.0

    print(current_total)
    print(cost)

    # New total
    new_total = round(current_total + cost,2)

    # Clear collection
    totals_col.delete_many({})

    # Insert new total
    bills_col.insert_one({"cost": cost})
    totals_col.insert_one({"total_spent": new_total})
    return redirect('/stats')



@app.route('/stats')
def stats():
    bill = bills_col.find_one(sort=[("_id", -1)])["cost"] # Get the latest bill
    total = totals_col.find_one()["total_spent"]
    return render_template('moni.html', price=bill, total=total)

# API Endpoints for Monthly Targets

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

# POST /api/targets  JSON: { "month": "YYYY-MM", "target": 123.45 }
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

# DELETE /api/targets?month=YYYY-MM
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
    app.run(host='0.0.0.0', port=port, debug=False)







