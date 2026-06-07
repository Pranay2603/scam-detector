import os
import time
import threading
import random
import smtplib
from email.mime.text import MIMEText
from authlib.integrations.flask_client import OAuth
from flask import Flask, render_template, request, redirect, url_for, session
from model.detector import analyze_text
from database.db import insert_history, get_all_history, delete_by_ids, delete_by_time, init_db, create_user, get_user, get_user_by_email, get_connection
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev_secret")

# ---------------- GOOGLE AUTH ----------------
oauth = OAuth(app)

app.config['GOOGLE_CLIENT_ID'] = os.getenv("GOOGLE_CLIENT_ID")
app.config['GOOGLE_CLIENT_SECRET'] = os.getenv("GOOGLE_CLIENT_SECRET")

google = oauth.register(
    name='google',
    client_id=app.config['GOOGLE_CLIENT_ID'],
    client_secret=app.config['GOOGLE_CLIENT_SECRET'],
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)

def send_otp_email(to_email, otp):
    import traceback
    sender_email = os.getenv("EMAIL_USER")
    app_password = os.getenv("EMAIL_PASS")

    print(f"[OTP] Attempting to send to {to_email}")
    print(f"[OTP] EMAIL_USER = {sender_email}")
    print(f"[OTP] EMAIL_PASS set = {bool(app_password)}")

    if not sender_email or not app_password:
        print("[OTP] ERROR: EMAIL_USER or EMAIL_PASS is missing from environment variables!")
        return

    subject = "Scam Detector - Password Reset OTP"
    body = f"""
    Your OTP for password reset is: {otp}

    This OTP is valid for 2 minutes.
    If you did not request this, ignore this email.
    """
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = f"Scam Detector <{sender_email}>"
    msg["To"] = to_email

    try:
        print("[OTP] Connecting to SMTP...")
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(sender_email, app_password)
        server.sendmail(sender_email, to_email, msg.as_string())
        server.quit()
        print("[OTP] Email sent successfully!")
    except Exception as e:
        print(f"[OTP] Email FAILED: {e}")
        traceback.print_exc()
    

# ---------------- INIT DB ----------------
init_db()


# ---------------- LANDING PAGE ----------------
@app.route("/")
def landing():
    return render_template("landing.html")


# ---------------- DASHBOARD ----------------
@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "user" not in session:
        return redirect("/login")

    prefill_text = request.args.get("text", "")

    if request.method == "POST":
        user_text = request.form["text"]

        if not user_text.strip():
            return render_template("index.html", result=None, error="Please enter a message")

        time.sleep(1.5)
        result = analyze_text(user_text)
        result["text"] = user_text

        insert_history(user_text, result["score"], result["risk"], session["user"])

        return render_template("index.html", result=result)

    return render_template("index.html", result=None, prefill_text=prefill_text)


# ---------------- RESULT ----------------
@app.route("/result")
def result_page():
    if "user" not in session:
        return redirect("/login")

    text = request.args.get("text")
    result = analyze_text(text)

    return render_template("index.html", result=result)


# ---------------- HISTORY ----------------
@app.route("/history")
def show_history():
    if "user" not in session:
        return redirect("/login")

    history = get_all_history(session["user"])
    return render_template("history.html", history=history)


# ---------------- DELETE ----------------
@app.route("/delete-selected", methods=["POST"])
def delete_selected():
    if "user" not in session:
        return redirect("/login")

    selected = request.form.getlist("selected")

    if selected:
        delete_by_ids(selected)

    return redirect("/history")


@app.route("/delete-range/<int:hours>")
def delete_range(hours):
    if "user" not in session:
        return redirect("/login")

    delete_by_time(hours)
    return redirect("/history")


# ---------------- GOOGLE LOGIN ----------------
@app.route("/google-login")
def google_login():
    redirect_uri = url_for('callback', _external=True)
    return google.authorize_redirect(redirect_uri)


@app.route("/callback")
def callback():
    token = google.authorize_access_token()

    resp = google.get("https://www.googleapis.com/oauth2/v1/userinfo")
    user_info = resp.json()

    email = user_info["email"]
    name = user_info.get("name", email)

    # 🔥 CHECK IF USER EXISTS
    user = get_user_by_email(email)

    # 🔥 IF NOT → CREATE USER
    if not user:
        create_user(name, "", email)

    # 🔥 LOGIN USER
    session["user"] = email

    return redirect("/dashboard")


# ---------------- SIGNUP ----------------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        email = request.form["email"]

        success = create_user(username, password, email)

        if not success:
            return render_template("signup.html", error="Username already exists")

        return redirect("/login")

    return render_template("signup.html")


# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = get_user(username, password)

        if not user:
            return render_template("login.html", error="Invalid credentials")

        session["user"] = user[0]
        return redirect("/dashboard")

    reset = request.args.get("reset")
    return render_template(
        "login.html",
        success="Password reset successful" if reset else None
    )


# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/")

@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form["email"]

        user = get_user_by_email(email)

        if not user:
            return render_template("forgot.html", error="No account found with this email")

        otp = str(random.randint(100000, 999999))

        session["reset_email"] = email
        session["otp"] = otp
        session["otp_time"] = time.time()
        session["otp_attempts"] = 0

        threading.Thread(target=send_otp_email, args=(email, otp)).start()

        return redirect(url_for("verify_otp", email=email))

    return render_template("forgot.html")

@app.route("/verify-otp", methods=["GET", "POST"])
def verify_otp():
    email = session.get("reset_email")

    if not email:
        return redirect("/forgot-password")

    if request.method == "POST":
        entered_otp = request.form["otp"]

        stored_otp = session.get("otp")
        otp_time = session.get("otp_time")

        attempts = session.get("otp_attempts", 0)

        # 🚫 block after 5 tries
        if attempts >= 5:
            session.pop("otp", None)
            session.pop("otp_attempts", None)

            return render_template(
                "verify_otp.html",
                error="Too many attempts, Please go back and request a new OTP.",
                otp_time=session.get("otp_time")
            )

        # ⏱ Expiry check (2 minutes)
        if not otp_time or time.time() - otp_time > 120:
            session.pop("otp", None)
            return render_template(
                "verify_otp.html", 
                error="OTP expired. Please request a new one.",
                otp_time=session.get("otp_time")
            )

        # ✅ OTP match (safe check added)
        if stored_otp and entered_otp == stored_otp:
            session.pop("otp", None)                      
            session.pop("otp_time", None)
            session.pop("otp_attempts", None)
            return redirect(url_for("reset_password", email=email))

        session["otp_attempts"] = attempts + 1
        return render_template(
            "verify_otp.html",
            error="Invalid OTP",
            otp_time=session.get("otp_time")
        )

    return render_template("verify_otp.html", otp_time=session.get("otp_time"))

@app.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    email = session.get("reset_email")

    if not email:
        return redirect("/forgot-password")

    if request.method == "POST":
        new_password = request.form["password"]

        from werkzeug.security import generate_password_hash
        hashed_password = generate_password_hash(new_password)

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "UPDATE users SET password = ? WHERE email = ?",
            (hashed_password, email)
        )

        conn.commit()
        conn.close()

        # 🔥 clear session after reset
        session.pop("reset_email", None)

        return render_template("login.html", success="Password reset successful")

    return render_template("reset_password.html")

# ---------------- RUN ----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)