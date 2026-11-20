import pickle
from flask import Flask, render_template, request, redirect, session
import os
import sqlite3
from datetime import datetime
import pytesseract
from PIL import Image
import requests
from bs4 import BeautifulSoup
from openai import OpenAI

# from transformers import pipeline
from dotenv import load_dotenv
load_dotenv()

GROK_API_KEY = os.getenv("GROK_API_KEY")
FACT_CHECK_API_KEY = os.getenv("FACT_CHECK_API_KEY")

client = OpenAI(
    api_key=GROK_API_KEY,
    base_url="https://api.x.ai/v1",
)
# ================= BASIC =================
app = Flask(__name__)
app.secret_key = "secret123"

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

print("DB PATH:", os.path.abspath('database.db'))

# ================= DATABASE =================
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT UNIQUE,
        password TEXT,
        mobile TEXT
    )
    ''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        news TEXT,
        result TEXT,
        user_id INTEGER,
        date TEXT
    )
    ''')

    conn.commit()
    conn.close()

init_db()

# ================= LOAD MODEL =================
model = pickle.load(open("models/svm_model.pkl", "rb"))
vectorizer = pickle.load(open("models/vectorizer.pkl", "rb"))

import re

def clean_text(text):
    text = text.lower()
    text = re.sub(r"http\S+", "", text)
    text = re.sub(r"[^a-zA-Z ]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text


# def svm_predict(text):

#     text = clean_text(text)

#     vec = vectorizer.transform([text])
#     pred = model.predict(vec)[0]

#     # 🔥 REAL CONFIDENCE
#     decision = model.decision_function(vec)[0]
#     confidence = min(95, max(60, int(abs(decision) * 20)))

#     if pred == 1:
#         return "Real News", confidence, "Language patterns match verified news articles", ""
#     else:
#         return "Fake News", confidence, "Detected misleading or non-credible language patterns", ""
    

def grok_analyze_news(text):

    try:

        response = client.chat.completions.create(
            model="grok-3",
            messages=[
                {
                    "role": "system",
                    "content": """
                    You are a fake news detection AI.

                    Analyze the news carefully.

                    Return:
                    1. Verdict (Real/Fake/Suspicious)
                    2. Short reason
                    """
                },
                {
                    "role": "user",
                    "content": text
                }
            ],
            temperature=0.2
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"Grok API Error: {str(e)}"
    

FACT_CHECK_API_KEY = os.getenv("FACT_CHECK_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

print("NEWS API KEY:", NEWS_API_KEY)
print("FACT CHECK API KEY:", FACT_CHECK_API_KEY)
def fact_check_news(query):

    url = f"https://factchecktools.googleapis.com/v1alpha1/claims:search?query={query}&key={FACT_CHECK_API_KEY}"

    try:

        response = requests.get(url)
        data = response.json()

        claims = data.get("claims")

        if claims:

            first_claim = claims[0]

            text = first_claim.get("text", "No claim text")

            claimant = first_claim.get("claimant", "Unknown")

            review = first_claim.get("claimReview", [{}])[0]

            rating = review.get("textualRating", "No rating")

            return {
                "found": True,
                "claim": text,
                "claimant": claimant,
                "rating": rating
            }

        else:
            return {"found": False}

    except Exception as e:
        return {"error": str(e)}


def predict_news(text):

    text = clean_text(text)

    vec = vectorizer.transform([text])

    pred = model.predict(vec)[0]
    prob = model.predict_proba(vec)[0]

    confidence = int(max(prob) * 100)

    if pred == 1:
        return "Real News", confidence, "Based on statistical language patterns", ""
    else:
        return "Fake News", confidence, "Detected misleading language patterns", ""

def extract_from_url(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0"
        }

        response = requests.get(url, headers=headers, timeout=5)

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.text, "html.parser")

        paragraphs = soup.find_all("p")
        text = " ".join([p.get_text() for p in paragraphs])

        return text.strip()

    except:
        return None

NEWS_API_KEY = os.getenv("NEWS_API_KEY")

# =============================
# 🔥 GOOGLE CURRENT NEWS SEARCH
# =============================

def search_current_news(text):

    try:

        query = "+".join(text.split()[:8])

        url = f"https://www.google.com/search?q={query}+news"

        headers = {
            "User-Agent": "Mozilla/5.0"
        }

        response = requests.get(url, headers=headers)

        html = response.text.lower()

        print("GOOGLE SEARCH SUCCESS")

        keywords = text.lower().split()[:5]

        match_count = 0

        for word in keywords:

            if word in html:
                match_count += 1

        print("MATCH COUNT:", match_count)

        if match_count >= 3:
            return True

        return False

    except Exception as e:

        print("GOOGLE SEARCH ERROR:", e)

        return False
# ================= ROUTES =================

@app.route("/")
def home():

    # If user is logged in AND is admin → redirect
    if "user_id" in session and session.get("role") == "admin":
        return redirect("/admin")

    return render_template("index.html")

@app.route('/detect', methods=['GET', 'POST'])
def detect():
    if request.method == "POST":

        text = request.form["news"]
        category = request.form.get("category")

        # 🔥 MODEL PREDICTION
        result = predict_news(text)

        # 🔥 ADD TIMESTAMP
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 🔥 SAVE TO DATABASE
        conn = sqlite3.connect("database.db")
        c = conn.cursor()

        c.execute(
            "INSERT INTO history (news, result, user_id, date, category, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
        (
               text,
               result,
               session["user_id"],
               datetime.now().strftime("%Y-%m-%d %H:%M"),
               category,
               datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
   )

        conn.commit()
        conn.close()

        return render_template('detect.html', result=result)

    return render_template('detect.html')


# ================= PREDICT =================

@app.route('/predict', methods=['POST'])
def predict():

    text = request.form.get('news')
    category = request.form.get("category")

    if not category:
        category = "General"

    print("CATEGORY:", category)

    url = request.form.get('url')
    image = request.files.get('image')

    final_text = ""

    # 🔒 CHECK LOGIN STATUS
    is_logged_in = session.get('user_id')

    # =============================
    # ✅ TEXT INPUT
    # =============================
    if text and text.strip():
        final_text = text.strip()

    # =============================
    # ✅ URL INPUT
    # =============================
    elif url and url.strip():

        if not is_logged_in:
            return render_template(
                "detect.html",
                error="🔒 URL feature available for logged-in users only"
            )

        final_text = extract_from_url(url)

        if not final_text or len(final_text.split()) < 20:
            return render_template(
                "detect.html",
                error="⚠️ Unable to extract readable article content"
            )

    # =============================
    # ✅ IMAGE INPUT
    # =============================
    elif image and image.filename != "":

        if not is_logged_in:
            return render_template(
                "detect.html",
                error="🔒 Image upload available for logged-in users only"
            )

        try:
            img = Image.open(image)
            final_text = pytesseract.image_to_string(img, config='--psm 6')

        except:
            return render_template(
                "detect.html",
                error="Image processing failed"
            )

    final_text = final_text.replace("\n", " ").strip()

    if not final_text:
        return render_template(
            "detect.html",
            error="No readable text found"
        )

    # =============================
    # 🔥 INPUT VALIDATION
    # =============================
    if len(final_text.split()) < 5:
        return render_template(
            "detect.html",
            error="⚠️ Enter meaningful news text"
        )

    if len(final_text) > 5000:
        return render_template(
            "detect.html",
            error="⚠️ Text too long (max 5000 chars)"
        )

    if len(set(final_text.split())) < 3:
        return render_template(
            "detect.html",
            error="⚠️ Invalid or repetitive text"
        )

    # # =============================
    # # 🔥 RULE-BASED CHECKS
    # # =============================
    # text_lower = final_text.lower()

    # crime_keywords = [
    #     "murder", "accident", "kidnap", "robbery",
    #     "police", "arrested", "crime", "attack",
    #     "injured", "hospitalized", "earthquake",
    #     "flood", "fire broke out", "whatsapp notice",
    #     "district administration", "government notice"
    # ]

    # fake_keywords = [
    #     "aliens landed", "invisible",
    #     "free iphone", "magic cure",
    #     "6 days darkness", "human can fly",
    #     "drink bleach"
    # ]

    # viral_patterns = [
    #     "forward this message",
    #     "share with everyone",
    #     "whatsapp forward",
    #     "viral message"
    # ]

    # # =============================
    # # ✅ RULE ENGINE
    # # =============================
    # if any(word in text_lower for word in crime_keywords):

    #     label = "Real News"
    #     confidence = 95
    #     reason = "Detected realistic breaking/crime news pattern"
    #     sub_label = "Rule-Based Detection"

    # elif any(word in text_lower for word in fake_keywords):

    #     label = "Fake News"
    #     confidence = 99
    #     reason = "Detected impossible or viral fake pattern"
    #     sub_label = "Rule-Based Detection"

    # elif any(word in text_lower for word in viral_patterns):

    #     label = "Suspicious"
    #     confidence = 75
    #     reason = "Detected viral forward pattern"
    #     sub_label = "Rule-Based Detection"


    
    # =============================
    # 🤖 SVM MODEL
    # =============================
    # else:

        # label, confidence, reason, sub_label = predict_news(final_text)

        # # =============================
        # # 🔥 AI + FACT CHECK
        # # =============================
        # if confidence < 85:

        #     grok_result = grok_analyze_news(final_text)

        #     fact_result = fact_check_news(final_text[:200])

        #     # 🔥 GROK OVERRIDE
        #     if "fake" in grok_result.lower():

        #         label = "Fake News"
        #         reason = "Grok AI detected misleading or suspicious content"

        #     elif "real" in grok_result.lower():

        #         label = "Real News"

        #     # 🔥 FACT CHECK OVERRIDE
        #     if fact_result.get("found"):

        #         rating = fact_result.get("rating", "").lower()

        #         if "false" in rating:

        #             label = "Fake News"
        #             reason = "Matched false claim from fact-check database"

        #         elif "true" in rating:

        #             label = "Real News"
        #             reason = "Matched verified claim from fact-check database"
    
    # =============================

    # =============================
# 🤖 SVM MODEL
    # =============================

    label, confidence, reason, sub_label = predict_news(final_text)

# =============================
# 🔥 GROK AI ANALYSIS
# =============================

    grok_result = grok_analyze_news(final_text)

# =============================
# 🔥 FACT CHECK API
# =============================

    fact_result = fact_check_news(final_text[:200])

# =============================
# 🔥 CURRENT NEWS SEARCH
# =============================

    current_news = search_current_news(final_text)
    print("CURRENT NEWS FOUND:", current_news)
    # =============================
# ✅ CURRENT NEWS BOOST
# =============================

    if current_news and confidence < 80:

       label = "Real News"
       confidence = 90
       reason = "Matched live current affairs/news sources"
# =============================
# ✅ GROK AI OVERRIDE
# =============================

    elif grok_result and confidence < 80:

      grok_result = grok_result.lower()

      if "fake" in grok_result:

        label = "Fake News"
        confidence = 95
        reason = "Grok AI detected misleading or suspicious content"

      elif "real" in grok_result:

        label = "Real News"
        confidence = 95
        reason = "Grok AI verified realistic news content"

# =============================
# ✅ FACT CHECK OVERRIDE
# =============================

    if fact_result and fact_result.get("found"):

      rating = fact_result.get("rating", "").lower()

      if "false" in rating:

        label = "Fake News"
        confidence = 99
        reason = "Matched verified false claim from fact-check database"

      elif "true" in rating:

        label = "Real News"
        confidence = 99
        reason = "Matched verified true claim from fact-check database"

# =============================
# 🔥 FINAL DEBUG
# =============================

    print("FINAL:", label, confidence)

# =============================
# 🔥 GUEST LIMIT
# =============================

    if not session.get('user_id'):

       today = datetime.now().strftime("%Y-%m-%d")

       if session.get('guest_date') != today:
        session['guest_date'] = today
        session['guest_count'] = 0

       if session.get('guest_count', 0) >= 3:

        return render_template(
            "detect.html",
            error="⚠️ Free limit reached (3/day). Please login."
        )

    session['guest_count'] = session.get('guest_count', 0) + 1

    # print("FINAL:", label, confidence)
    # news_exists = search_current_news(final_text[:100])
    # if news_exists and confidence < 85:

    #    label = "Real News"
    #    confidence = 90
    #    reason = "Similar current news found from trusted sources"
    # =============================
    # 🔥 GUEST LIMIT
    # =============================
    if not session.get('user_id'):

        today = datetime.now().strftime("%Y-%m-%d")

        if session.get('guest_date') != today:
            session['guest_date'] = today
            session['guest_count'] = 0

        if session.get('guest_count', 0) >= 3:

            return render_template(
                "detect.html",
                error="⚠️ Free limit reached (3/day). Please login."
            )

        session['guest_count'] = session.get('guest_count', 0) + 1

    # =============================
    # 🔥 USER DAILY LIMIT
    # =============================
    if session.get('user_id'):

        conn = sqlite3.connect('database.db')
        c = conn.cursor()

        today = datetime.now().strftime("%Y-%m-%d")

        c.execute("""
            SELECT COUNT(*) FROM history
            WHERE user_id = ? AND date LIKE ?
        """, (session['user_id'], today + "%"))

        today_count = c.fetchone()[0]

        if today_count >= 50:

            conn.close()

            return render_template(
                "detect.html",
                error="⚠️ Daily limit reached (50 checks). Try tomorrow."
            )

        conn.close()

    # =============================
    # 🔥 SAVE HISTORY
    # =============================
    if session.get('user_id'):

        conn = sqlite3.connect('database.db')
        c = conn.cursor()

        c.execute(
            """
            INSERT INTO history
            (news, result, user_id, date, category, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                final_text,
                label,
                session['user_id'],
                datetime.now().strftime("%Y-%m-%d %H:%M"),
                category,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
        )

        conn.commit()
        conn.close()

    # =============================
    # 🔥 RESULT UI
    # =============================
    if label == "Real News":

        prediction_class = "real"
        icon = "✅"

    elif label == "Fake News":

        prediction_class = "fake"
        icon = "❌"

    elif label == "Suspicious":

        prediction_class = "suspicious"
        icon = "⚠️"

    else:

        prediction_class = ""
        icon = ""

    return render_template(
        "result.html",
        prediction=label,
        confidence=confidence,
        news=final_text,
        reason=reason,
        sub_label=sub_label,
        prediction_class=prediction_class,
        icon=icon
    )


# ================= HISTORY =================

@app.route('/history')
def history():

    if 'user_id' not in session:
        return redirect('/login')

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute("SELECT * FROM history WHERE user_id=? ORDER BY id DESC", (session['user_id'],))
    data = c.fetchall()
    
    real_count = sum(1 for i in data if "Real" in i[2])
    fake_count = sum(1 for i in data if "Fake" in i[2])

    conn.close()

    return render_template('history.html', data=data, real_count=real_count, fake_count=fake_count)

# ================= DELETE =================

@app.route('/delete/<int:id>', methods=['POST'])
def delete(id):

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute("DELETE FROM history WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return redirect('/history')

# ================= REGISTER =================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        phone = request.form["phone"]

        # Name Validation
        if not re.match(r"^[A-Za-z ]{3,50}$", name):
            return render_template(
                "register.html",
                error="Invalid name"
            )

        # Email Validation
        if not re.match(
            r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$",
            email
        ):
            return render_template(
                "register.html",
                error="Invalid email address"
            )

        # Mobile Validation
        if not re.match(r"^[0-9]{10}$", phone):
            return render_template(
                "register.html",
                error="Mobile number must contain exactly 10 digits"
            )

        # Password Validation
        if len(password) < 6:
            return render_template(
                "register.html",
                error="Password must be at least 6 characters"
            )

        conn = sqlite3.connect("database.db")
        c = conn.cursor()

        # Check if user already exists
        c.execute("SELECT * FROM users WHERE email=?", (email,))
        existing_user = c.fetchone()

        if existing_user:
            conn.close()
            return render_template("register.html", msg="Email already registered ❌")

        # Insert new user
        c.execute(
            "INSERT INTO users (name, email, password, phone) VALUES (?, ?, ?, ?)",
            (name, email, password, phone)
        )

        conn.commit()
        conn.close()

        # ✅ REDIRECT TO LOGIN WITH SUCCESS MESSAGE
        return redirect("/login?success=1")

    return render_template("register.html")
# ================= LOGIN =================

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        email = request.form['email'].strip().lower()
        password = request.form['password'].strip()

        conn = sqlite3.connect('database.db')
        c = conn.cursor()

        c.execute("SELECT * FROM users WHERE email=? AND password=?", (email, password))
        user = c.fetchone()

        conn.close()

        if user:
            session['user'] = user[1]
            session['user_id'] = user[0]
            session["role"] = user[5]
            if user[5] == "admin":
               return redirect("/admin")
            else:
               return redirect("/")

        return render_template('login.html', msg="Invalid credentials")

    return render_template('login.html')

# ================= LOGOUT =================

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


# ================= RUN =================
@app.route('/profile')
def profile():

    if not session.get('user_id'):
        return redirect('/login')

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    # USER INFO
    c.execute("SELECT name, email FROM users WHERE id=?", (session['user_id'],))
    user = c.fetchone()

    # HISTORY STATS
    c.execute("SELECT COUNT(*) FROM history WHERE user_id=?", (session['user_id'],))
    total = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM history WHERE result='Real News' AND user_id=?", (session['user_id'],))
    real = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM history WHERE result='Fake News' AND user_id=?", (session['user_id'],))
    fake = c.fetchone()[0]

    conn.close()

    return render_template(
        "profile.html",
        user_name=user[0],
        user_email=user[1],
        total_checks=total,
        real_count=real,
        fake_count=fake
    )



# -------------------- ADMIN PANEL --------------------
@app.route('/admin')
def admin():

    if session.get("role") != "admin":
        return redirect('/')

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    # 📊 COUNTS
    c.execute("SELECT COUNT(*) FROM users")
    total_users = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM history")
    total_checks = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM history WHERE result='Real News'")
    real_count = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM history WHERE result='Fake News'")
    fake_count = c.fetchone()[0]

    # 📊 CATEGORY DISTRIBUTION (CLEAN DATA)
    c.execute("""
        SELECT category, COUNT(*) 
        FROM history 
        WHERE category IS NOT NULL 
        AND category != '' 
        AND category != 'Unknown'
        GROUP BY category
        ORDER BY COUNT(*) DESC
    """)
    categories = c.fetchall()

    # 📊 MONTHLY TOP CATEGORY
    current_month = datetime.now().strftime("%Y-%m")

    c.execute("""
        SELECT category, COUNT(*) 
        FROM history
        WHERE date LIKE ?
        AND category IS NOT NULL 
        AND category != '' 
        AND category != 'Unknown'
        GROUP BY category
        ORDER BY COUNT(*) DESC
        LIMIT 1
    """, (current_month + "%",))

    top_category = c.fetchone()

    # 🔍 FILTERS
    category_filter = request.args.get('category')
    result_filter = request.args.get('result')

    query = """
        SELECT news, category, result, date 
        FROM history 
        WHERE 1=1
    """
    params = []

    if category_filter:
        query += " AND category = ?"
        params.append(category_filter)

    if result_filter:
        query += " AND result = ?"
        params.append(result_filter)

    query += " ORDER BY id DESC LIMIT 10"

    c.execute(query, params)
    history = c.fetchall()

    # ✅ CLOSE ONLY HERE
    conn.close()

    return render_template(
        "admin.html",
        total_users=total_users,
        total_checks=total_checks,
        real_count=real_count,
        fake_count=fake_count,
        categories=categories,
        history=history,
        top_category=top_category
    )
@app.route('/admin/users')
def admin_users():

    if session.get("role") != "admin":
        return redirect('/')

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute("""
        SELECT id, name, email, role
        FROM users
        ORDER BY role DESC, id ASC
    """)

    users = c.fetchall()

    conn.close()

    return render_template(
        "admin_users.html",
        users=users
    )

@app.route('/delete_user/<int:user_id>')
def delete_user(user_id):

    if session.get("role") != "admin":
        return redirect('/')

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute(
        "SELECT role FROM users WHERE id=?",
        (user_id,)
    )

    user = c.fetchone()

    if user:

        # Prevent deleting admin accounts
        if user[0] == "admin":

            conn.close()

            return """
            <script>
            alert('Admin accounts cannot be deleted');
            window.location='/admin/users';
            </script>
            """

        c.execute(
            "DELETE FROM users WHERE id=?",
            (user_id,)
        )

        conn.commit()

    conn.close()

    return redirect('/admin/users')
# -------------------- RUN --------------------
if __name__ == "__main__":
    app.run(debug=True)
