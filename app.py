import os
from flask import Flask, render_template, request, redirect, url_for, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


# -------------------- DATABASE MODEL --------------------
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# -------------------- QUESTIONS --------------------
questions = {
    "stress": [
        "I feel overwhelmed.",
        "I struggle to relax.",
        "I feel irritated easily."
    ]
}


# -------------------- ROUTES --------------------

@app.route("/")
def home():
    return render_template("index.html")


# REGISTER
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        if not username or not password:
            return "Please fill all fields"

        # Check if user already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return "Username already exists"

        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for("login"))

    return render_template("register.html")


# LOGIN
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        user = User.query.filter_by(username=username).first()

        if user and user.password == password:
            login_user(user)
            return redirect(url_for("select"))

        return "Invalid username or password"

    return render_template("login.html")


# LOGOUT
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))


# SELECT PAGE
@app.route("/select")
@login_required
def select():
    return render_template("select.html")


# QUIZ PAGE
@app.route("/quiz/<topic>")
@login_required
def quiz(topic):

    # Prevent KeyError
    if topic not in questions:
        abort(404)

    return render_template("quiz.html",
                           topic=topic,
                           questions=questions[topic])


# RESULT PAGE
@app.route("/result/<topic>", methods=["POST"])
@login_required
def result(topic):

    if topic not in questions:
        abort(404)

    score = 0
    total = len(questions[topic]) * 4

    for i in range(len(questions[topic])):
        score += int(request.form.get(f"q{i}", 0))

    percentage = (score / total) * 100

    if percentage <= 30:
        level = "Low"
        exercises = [
            "Light stretching",
            "15 min walking",
            "Gratitude journaling"
        ]
    elif percentage <= 60:
        level = "Moderate"
        exercises = [
            "20 min meditation",
            "Deep breathing",
            "Reduce screen time"
        ]
    else:
        level = "High"
        exercises = [
            "Daily yoga",
            "Muscle relaxation",
            "Consult counselor"
        ]

    return render_template("result.html",
                           percentage=round(percentage, 2),
                           level=level,
                           exercises=exercises)



if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
