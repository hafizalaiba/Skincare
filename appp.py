from flask import make_response
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from flask import session, redirect
from flask import Flask, request, jsonify, render_template
import cv2
from flask import redirect, url_for
import re

import numpy as np
from datetime import datetime
import os
import sqlite3
from PIL import Image
from flask_cors import CORS
from PIL import ImageDraw
import random


app = Flask(__name__, static_folder='static', static_url_path='/static')
app.secret_key = 'your_secret_key_here'  
CORS(app, supports_credentials=True) 
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def create_table():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    # Create tables only if they don't exist
    c.execute('''CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT,
    password TEXT
);

   ''')
    

    c.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            date TEXT,
            skin_type TEXT,
            acne_detected INTEGER,
            recommendation TEXT,
            image_path TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    conn.commit()
    conn.close()
    import random

def generate_analysis():
    concerns = [
        {"name": "acne", "severity": ["mild", "moderate", "severe"]},
        {"name": "wrinkles", "severity": ["early", "moderate", "deep"]},
        {"name": "dark spots", "severity": ["light", "noticeable", "pronounced"]},
        {"name": "redness", "severity": ["mild", "moderate", "severe"]},
        {"name": "pores", "severity": ["enlarged", "visible", "clogged"]}
    ]
    skin_types = [
        {"type": "normal", "note": "well-balanced"},
        {"type": "dry", "note": "dehydrated"},
        {"type": "oily", "note": "excess sebum"},
        {"type": "combination", "note": "mix of dry/oily areas"}
    ]

    concern = random.choice(concerns)
    severity = random.choice(concern["severity"])
    skin_type = random.choice(skin_types)

    return {
        "concern": concern["name"],
        "severity": severity,
        "skin_type": skin_type["type"],
        "note": skin_type["note"],
        "hydration": random.choice(["Adequate", "Could be improved"]),
        "texture": random.choice(["Smooth", "Uneven"])
    }
@app.route('/analyzeImage', methods=['POST'])
def analyze_image():
    user_id = session.get('user_id')
    # if not user_id:
    #     return jsonify({"error": "Not logged in"}), 401

    if 'image' not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    image = request.files['image']
    filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{image.filename}"
    image_path = os.path.join(UPLOAD_FOLDER, filename)
    image.save(image_path)

    analysis = generate_analysis()


    acne_detected = 1 if analysis["concern"] == "acne" else 0
    # Add botResponses-style description and solution
    concern_key = analysis["concern"]
    skin_key = analysis["skin_type"] + " skin"

    botResponses = {
      "dry skin": {
        "solution": "For dry skin treatment:<br>1. <strong>Gentle Cleanser</strong>: Avoid sulfates<br>2. <strong>Ceramide Moisturizer</strong>: CeraVe works best<br>3. <strong>Hydrating Serum</strong>: With hyaluronic acid<br>4. <strong>Occlusive</strong>: At night to lock in moisture"
    },
      
      "combination skin": {
    "solution": "For combination skin management:<br>1. <strong>Gentle Cleanser</strong>: Balances oily and dry areas<br>2. <strong>Hydrating Toner</strong>: Adds moisture without heaviness<br>3. <strong>Lightweight Moisturizer</strong>: Gel-based for T-zone, cream for dry areas<br>4. <strong>Niacinamide Serum</strong>: Controls oil and improves texture"
},

"normal skin": {
    "solution": "For normal skin maintenance:<br>1. <strong>Gentle Cleanser</strong>: Maintains skin balance<br>2. <strong>Hydrating Toner</strong>: Refreshes and tones<br>3. <strong>Light Moisturizer</strong>: Keeps skin soft and smooth<br>4. <strong>Sunscreen (SPF 30+)</strong>: Protects against UV damage"
},


      "acne": {
        "solution": "For acne treatment:<br>1. <strong>Salicylic Acid Cleanser</strong> (AM/PM)<br>2. <strong>Benzoyl Peroxide</strong> (spot treatment)<br>3. <strong>Non-comedogenic Moisturizer</strong><br>4. <strong>Retinol</strong> (PM, start weekly)"
    },
        "wrinkles": {
        "solution": "For anti-aging:<br>1. <strong>Vitamin C Serum</strong> (AM)<br>2. <strong>Retinol</strong> (PM, start slow)<br>3. <strong>Peptide Moisturizer</strong><br>4. <strong>SPF 30+ Daily</strong>"
    },
        "sensitive skin": {
        "solution": "For sensitive skin care:<br>1. <strong>Fragrance-Free Products</strong><br>2. <strong>Soothing Ingredients</strong>: Ceramides, oat<br>3. <strong>Patch Test</strong> new products<br>4. <strong>Minimal Routine</strong>: Cleanse, moisturize, SPF"
    }
}

# Use concern first, fallback to skin type
    solution = botResponses.get(concern_key, {}).get("solution") or botResponses.get    (skin_key, {}).get("solution") or "Use gentle skincare suitable for your skin type."

# Add to recommendation with line breaks
    recommendation = (
     f"<strong>Skin Type:</strong> {analysis['skin_type'].capitalize()} ({analysis['note']})<br>"
     f"<strong>Concern:</strong> {analysis['severity']} {analysis['concern']}<br>"
     f"<strong>Hydration:</strong> {analysis['hydration']}<br>"
     f"<strong>Texture:</strong> {analysis['texture']}<br><br>"
     f"<strong>Suggested Routine:</strong><br>{solution}"
)

   # Optionally use botResponses from JS, or construct similar string
# recommendation = (
#     f"<strong>Skin Type:</strong> {analysis['skin_type'].capitalize()} ({analysis['note']})<br>"
#     f"<strong>Concern:</strong> {analysis['severity']} {analysis['concern']}<br>"
#     f"<strong>Hydration:</strong> {analysis['hydration']}<br>"
#     f"<strong>Texture:</strong> {analysis['texture']}<br>"
# )


    # Save to DB
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute('''
        INSERT INTO history (user_id, date, skin_type, acne_detected, recommendation, image_path)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        user_id,
        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        analysis["skin_type"],
        acne_detected,
        recommendation,
        os.path.join('static/uploads', filename)
    ))
    conn.commit()
    conn.close()

    return jsonify({
    "skin_type": analysis["skin_type"],
    "note": analysis["note"],
    "acne_detected": bool(acne_detected),
    "severity": analysis["severity"],
    "hydration": analysis["hydration"],
    "texture": analysis["texture"],
    "recommendation": recommendation
})

@app.route('/delete-history/<int:history_id>', methods=['DELETE'])
def delete_history(history_id):
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Not logged in"}), 401

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    # 🧹 Step 1: Fetch the image path for cleanup
    c.execute("SELECT image_path FROM history WHERE id = ? AND user_id = ?", (history_id, user_id))
    result = c.fetchone()
    if not result:
        conn.close()
        return jsonify({"error": "Report not found"}), 404

    image_path = os.path.join(os.getcwd(), result[0].lstrip("/"))
    if os.path.exists(image_path):
        os.remove(image_path)

    #  Step 2: Delete from database
    c.execute("DELETE FROM history WHERE id = ? AND user_id = ?", (history_id, user_id))
    conn.commit()
    conn.close()

    return jsonify({"message": "History deleted"})
@app.route('/download-report/<int:history_id>')
def download_report(history_id):
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Not logged in"}), 401

    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT date, skin_type, acne_detected, recommendation, image_path FROM history WHERE id = ? AND user_id = ?", (history_id, user_id))
    record = c.fetchone()
    conn.close()

    if not record:
        return jsonify({"error": "Report not found"}), 404

    date, skin_type, acne_detected, recommendation, image_path = record
    acne_status = "Yes" if acne_detected else "No"

    response = make_response()
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=skin_report_{history_id}.pdf'

    pdf = canvas.Canvas(response.stream, pagesize=A4)

    # 🔵 CIRCULAR LOGO DRAW
    try:
        logo_path = os.path.join(os.getcwd(), "static", "uploads", "logo.png")
        logo_img = Image.open(logo_path).convert("RGBA")
        logo_w, logo_h = logo_img.size
        min_side = min(logo_w, logo_h)

        mask = Image.new("L", (min_side, min_side), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, min_side, min_side), fill=255)

        cropped = logo_img.crop(((logo_w - min_side) // 2, (logo_h - min_side) // 2,
                                 (logo_w + min_side) // 2, (logo_h + min_side) // 2))
        circular_logo = Image.new("RGBA", (min_side, min_side))
        circular_logo.paste(cropped, (0, 0), mask=mask)

        circular_logo_path = os.path.join("static", "uploads", "temp_circular_logo.png")
        circular_logo.save(circular_logo_path)

        # Place logo in PDF
        pdf_size = min_side * 0.5
        pdf.drawImage(circular_logo_path, 450, 710, width=pdf_size * 0.25, height=pdf_size * 0.25, mask='auto')

    except Exception as e:
        print("Circular logo error:", e)
        circular_logo_path = None

    # 📝 REPORT DETAILS
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(100, 770, " Skin Analysis Report")
    pdf.setFont("Helvetica", 12)
    pdf.drawString(100, 730, f"Date: {date}")
    pdf.drawString(100, 710, f"Skin Type: {skin_type}")
    pdf.drawString(100, 690, f"Acne Detected: {acne_status}")

    # 🧴 RECOMMENDATION (CLEANED)
    pdf.setFont("Helvetica", 12)
    pdf.drawString(100, 670, "Recommendation:")
    pdf.setFont("Helvetica", 11)

    cleaned_recommendation = re.sub(r'<br\s*/?>', '\n', recommendation or '', flags=re.IGNORECASE)
    cleaned_recommendation = re.sub(r'<[^>]+>', '', cleaned_recommendation)
    text_lines = cleaned_recommendation.strip().split('\n')

    y = 650
    for line in text_lines:
        if y < 100:
            break  # prevent text from overflowing page
        pdf.drawString(120, y, line.strip())
        y -= 15

    # 🖼️ SKIN IMAGE
    try:
        image_full_path = os.path.join(os.getcwd(), image_path.lstrip("/"))
        original_img = Image.open(image_full_path)
        img_w, img_h = original_img.size
        pdf_img_w = img_w * 0.35
        pdf_img_h = img_h * 0.35

        if y - pdf_img_h < 50:
            y = 380  # move up if space is low
            
        pdf.drawImage(image_full_path, 100, y - pdf_img_h - 20, width=pdf_img_w, height=pdf_img_h)
    except Exception as e:
        print("Image draw error:", e)

    # ✅ Finish PDF
    pdf.save()

    # 🧹 Clean temp logo
    if circular_logo_path and os.path.exists(circular_logo_path):
        os.remove(circular_logo_path)

    return response

@app.route('/history')
def history():
    user_id = session.get('user_id')
    print(">>> Session User ID:", user_id)

    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute("SELECT * FROM history WHERE user_id = ?", (user_id,))
    rows = c.fetchall()
    print(">>> Rows fetched:", rows)

    conn.close()

    return jsonify([dict(row) for row in rows])
@app.route("/")
def home():
    return render_template("index.html")
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    name = data['name']
    email = data['email']
    password = data['password']

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute("SELECT * FROM users WHERE email = ?", (email,))
    existing_user = c.fetchone()
    if existing_user:
        conn.close()
        return jsonify({"error": "Email already registered"}), 400

    # Directly save password (insecure but as you requested)
    c.execute("INSERT INTO users (name, email, password) VALUES (?, ?, ?)", (name, email, password))
    conn.commit()

    user_id = c.lastrowid
    session['user_id'] = user_id
    conn.close()

    return jsonify({"message": "Registration successful"})
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE email=? AND password=?', (email, password))
    user = c.fetchone()
    conn.close()

    if user:
        session['user_id'] = user[0]
        session['email'] = user[2]  # adjust index if needed
        return jsonify({"message": "Login successful", "redirect": "/dashboard"})
    else:
        return jsonify({"error": "Invalid credentials"}), 401

@app.route('/check-session')
def check_session():
    return jsonify({"user_id": session.get("user_id")})

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))  # you can define this route to show login
    return render_template('file.html')
def detect_dark_circles(image):
    # Sample logic based on lower eye area brightness
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
    eye_region = gray[int(h * 0.6):int(h * 0.75), int(w * 0.3):int(w * 0.7)]
    darkness = eye_region.mean()
    return darkness < 80  # low brightness means dark circles

def detect_blackheads(image):
    return random.choice([True, False])  # simulate

def detect_dark_spots(image):
    return random.choice([True, False])  # simulate

if __name__ == '__main__':
    create_table()
    app.run(debug=True, port=5000)