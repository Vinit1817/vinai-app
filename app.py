from flask import Flask, render_template, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
import pickle
import numpy as np
import sqlite3

# -----------------------
# App Config
# -----------------------
app = Flask(__name__)
app.secret_key = "vinai_secret_key"

# Load trained ML model
model = pickle.load(open("addiction_model.pkl", "rb"))

accuracy = 0.87  # model accuracy display


# -----------------------
# Database Initialization
# -----------------------
def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # Predictions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            screen_time REAL,
            night_usage INTEGER,
            app_switching INTEGER,
            study_distraction REAL,
            result TEXT
        )
    """)

    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)

    conn.commit()
    conn.close()


init_db()


# -----------------------
# Home Page
# -----------------------
@app.route("/")
def home():
    if "user" not in session:
        return redirect("/login")
    return render_template("index.html")


# -----------------------
# Prediction Route
# -----------------------
@app.route("/predict", methods=["POST"])
def predict():

    screen = float(request.form["screen_time"])
    night = int(request.form["night_usage"])
    switch = int(request.form["app_switching"])
    distraction = float(request.form["study_distraction"])

    input_data = np.array([[screen, night, switch, distraction]])
    prediction = model.predict(input_data)[0]

    # Save to database
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO predictions 
        (screen_time, night_usage, app_switching, study_distraction, result)
        VALUES (?, ?, ?, ?, ?)
    """, (screen, night, switch, distraction, prediction))

    conn.commit()
    conn.close()

    # Recommendation Logic
    if prediction == "Low":
        color = "green"
        message = "Great! You maintain a healthy digital balance."
    elif prediction == "Moderate":
        color = "orange"
        message = "Try reducing screen time and avoid night usage."
    else:
        color = "red"
        message = "High addiction risk! Consider digital detox strategies."

    return render_template("index.html",
                           result=prediction,
                           color=color,
                           message=message,
                           accuracy=accuracy)


# -----------------------
# Register
# -----------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        try:
           hashed_password = generate_password_hash(password)

cursor.execute(
    "INSERT INTO users (username, password) VALUES (?, ?)",
    (username, hashed_password)
)
            conn.commit()
        except:
            conn.close()
            return "Username already exists"

        conn.close()
        return redirect("/login")

    return render_template("register.html")


# -----------------------
# Login
# -----------------------
@app.route("/profile")
def profile():
    if "user" not in session:
        return redirect("/login")
    return render_template("profile.html", username=session["user"])
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE username=?", (username,))
user = cursor.fetchone()

if user and check_password_hash(user[2], password):
    session["user"] = username
    return redirect("/")
else:
    return "Invalid Credentials"
            return redirect("/")
        else:
            return "Invalid Credentials"

    return render_template("login.html")


# -----------------------
# Logout
# -----------------------
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/login")


# -----------------------
# Dashboard
# -----------------------
@app.route("/dashboard")
def dashboard():

    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM predictions")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM predictions WHERE result='High'")
    high = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM predictions WHERE result='Moderate'")
    moderate = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM predictions WHERE result='Low'")
    low = cursor.fetchone()[0]

    conn.close()

    return render_template("dashboard.html",
                           total=total,
                           high=high,
                           moderate=moderate,
                           low=low)


# -----------------------
# Run Server
# -----------------------
if __name__ == "__main__":
    app.run(debug=True)