import os
from functools import wraps
from dotenv import load_dotenv
from flask import (
    Flask, render_template, request,
    redirect, url_for, session, flash
)
from supabase import create_client

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY")

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax"
)

URL = os.environ.get("SUPABASE_URL")
KEY = os.environ.get("SUPABASE_KEY")

def auth_client():
    # Simple client creation without complex options to avoid attribute errors
    return create_client(URL, KEY)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "access_token" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def home():
    return redirect(url_for('signup'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        try:
            client = auth_client()
            response = client.auth.sign_up({"email": email, "password": password})
            if response.session:
                session.clear()
                session["access_token"] = response.session.access_token
                return redirect(url_for('dashboard'))
            flash("Account created successfully! Please check your email to confirm if required, or login now.", "success")
            return redirect(url_for('login'))
        except Exception as error:
            flash(str(error), "error")
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        try:
            client = auth_client()
            response = client.auth.sign_in_with_password({"email": email, "password": password})
            if not response.session:
                raise ValueError("Login failed")
            session.clear()
            session["access_token"] = response.session.access_token
            return redirect(url_for('dashboard'))
        except Exception:
            flash("Login failed. Check your credentials and email verification.", "error")
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    token = session["access_token"]
    user = auth_client().auth.get_user(token).user
    return render_template('dashboard.html', email=user.email)

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)