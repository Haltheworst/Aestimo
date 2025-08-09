from time import timezone
import cv2
import re 
import os 
import easyocr
import warnings
import numpy as np
from dotenv import load_dotenv
from pymongo import MongoClient
from flask import Flask, flash, redirect, render_template, request, url_for

load_dotenv()

warnings.filterwarnings("ignore", message=".*pin_memory.*")

cluster =  MongoClient(os.getenv("MONOGOPASS"))
db = cluster["AestimoData"]
bills_col  = db["expense"]   # individual bills
totals_col = db["total"]   

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
    latest = totals_col.find_one()
    current_total = float(latest.get("total_spent", 0)) if latest else 0.0

    print(current_total)
    print(cost)

    # New total
    new_total = current_total + cost

    # Clear collection
    totals_col.delete_many({})

    # Insert new total
    totals_col.insert_one({"total_spent": new_total})

    return redirect(url_for('stats', bill=cost, total=new_total))



@app.route('/stats')
def stats():
    total = request.args.get('bill')
    return render_template('moni.html', price=total)
    print(total)
    
if __name__ == '__main__':
    app.run(debug=True)






