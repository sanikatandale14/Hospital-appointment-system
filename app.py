from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from models import db, User, Appointment
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = "hospital-secret"
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///hospital.db"

db.init_app(app)

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Workaround for Flask 3.x: create tables at startup
with app.app_context():
    db.create_all()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    error = None
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        role = request.form.get("role")
        phone = request.form.get("phone")

        if not username or not password or not role or not phone:
            error = "All fields are required. Please fill out the form completely."
        elif User.query.filter_by(username=username).first():
            error = "Username already exists. Please choose a different username."
        else:
            hashed_pw = generate_password_hash(password, method='pbkdf2:sha256')
            new_user = User(username=username, password=hashed_pw, role=role, phone=phone)
            db.session.add(new_user)
            db.session.commit()
            print(f"Registered user: {new_user.username}, role: {new_user.role}, id: {new_user.id}")
            login_user(new_user)
            print(f"Logged in user: {new_user.username}, authenticated: {new_user.is_authenticated}")
            return redirect(url_for("appointment"))
    return render_template("register.html", error=error)
# Add appointment route
@app.route("/appointment", methods=["GET", "POST"])
@login_required
def appointment():
    doctors = User.query.filter_by(role="doctor").all()
    if request.method == "POST":
        doctor_id = request.form.get("doctor")
        date = request.form.get("date")
        time = request.form.get("time")
        appointment = Appointment(patient_id=current_user.id, doctor_id=doctor_id, date=date, time=time)
        db.session.add(appointment)
        db.session.commit()
        # Send SMS to patient using Twilio
        try:
            from twilio.rest import Client
            # Replace with your Twilio credentials
            account_sid = 'YOUR_TWILIO_ACCOUNT_SID'
            auth_token = 'YOUR_TWILIO_AUTH_TOKEN'
            twilio_number = 'YOUR_TWILIO_PHONE_NUMBER'
            client = Client(account_sid, auth_token)
            patient = User.query.get(current_user.id)
            message = client.messages.create(
                body=f"Your appointment on {date} at {time} is successfully booked.",
                from_=twilio_number,
                to=patient.phone
            )
        except Exception as e:
            print(f"SMS sending failed: {e}")
        return redirect(url_for("dashboard"))
    return render_template("appointment.html", doctors=doctors)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("appointment"))
    return render_template("login.html")


from datetime import datetime

@app.route("/dashboard")
@login_required
def dashboard():
    today = datetime.now().date()
    today_str = today.strftime('%d %b %Y')
    all_doctors = User.query.filter_by(role="doctor").all()
    all_patients = User.query.filter_by(role="patient").all()
    recent_registrations = User.query.order_by(User.id.desc()).limit(5).all()
    if current_user.role == "patient":
        return render_template(
            "dashboard.html",
            doctors=all_doctors,
            patients=all_patients,
            recent_registrations=recent_registrations,
            role="patient",
            total_patients=len(all_patients),
            today_patients=0,
            today_appointments=0,
            today_date="",
            new_patients=0,
            old_patients=0,
            today_appointments_list=[],
            next_patient=None,
            current_user=current_user
        )
    elif current_user.role == "doctor":
        total_patients = len(all_patients)
        today_appointments_query = Appointment.query.filter_by(doctor_id=current_user.id, date=str(today)).all()
        today_appointments = len(today_appointments_query)
        today_patients = len(set([appt.patient_id for appt in today_appointments_query]))
        patient_ids = [appt.patient_id for appt in Appointment.query.filter_by(doctor_id=current_user.id).all()]
        new_patients = len(set(patient_ids))
        old_patients = total_patients - new_patients if total_patients > new_patients else 0
        today_appointments_list = []
        for appt in today_appointments_query:
            today_appointments_list.append({
                'patient_name': appt.patient.username,
                'reason': 'Health Checkup',
                'status': 'On Going'
            })
        next_patient = None
        if today_appointments_query:
            appt = today_appointments_query[0]
            next_patient = {
                'patient_name': appt.patient.username,
                'reason': 'Health Checkup',
                'patient_id': appt.patient.id,
                'dob': '15 Jan 1989',
                'sex': 'Male',
                'weight': '59',
                'height': '172',
                'tags': ['Asthma', 'Hypertension', 'Fever']
            }
        return render_template(
            "dashboard.html",
            doctors=all_doctors,
            patients=all_patients,
            recent_registrations=recent_registrations,
            total_patients=total_patients,
            today_patients=today_patients,
            today_appointments=today_appointments,
            today_date=today_str,
            new_patients=new_patients,
            old_patients=old_patients,
            today_appointments_list=today_appointments_list,
            next_patient=next_patient,
            current_user=current_user
        )

@app.route("/book/<int:doctor_id>", methods=["POST"])
@login_required
def book(doctor_id):
    if current_user.role != "patient":
        return redirect(url_for("dashboard"))
    date = request.form.get("date")
    time = request.form.get("time")
    appointment = Appointment(patient_id=current_user.id, doctor_id=doctor_id, date=date, time=time)
    db.session.add(appointment)
    db.session.commit()
    return redirect(url_for("dashboard"))

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)
