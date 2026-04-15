from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_wtf.csrf import CSRFProtect
from models import db, User, Department, Doctor, Patient, Appointment, Treatment, DoctorAvailability
from datetime import datetime, timedelta, date, time
from functools import wraps
import os

# Import blueprints (adjust import paths if you use a /routes or /blueprints folder)
from admin_routes import admin_bp
from patient_routes import patient_bp
from doctor_routes import doctor_bp

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SESSION_SECRET', 'dev-secret-key-change-in-production')

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hospital.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
csrf = CSRFProtect(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.context_processor
def inject_csrf_token():
    from flask_wtf.csrf import generate_csrf
    return dict(csrf_token=generate_csrf)

# You can keep non-role-specific routes here. For example:
@app.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin.admin_dashboard'))
        elif current_user.role == 'doctor':
            return redirect(url_for('doctor.doctor_dashboard'))
        elif current_user.role == 'patient':
            return redirect(url_for('patient.patient_dashboard'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password) and user.is_active:
            login_user(user)
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password, or account is inactive.', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        full_name = request.form.get('full_name')
        contact_number = request.form.get('contact_number')
        date_of_birth = request.form.get('date_of_birth')
        gender = request.form.get('gender')
        blood_group = request.form.get('blood_group')
        address = request.form.get('address')
        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'danger')
            return redirect(url_for('register'))
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return redirect(url_for('register'))
        user = User(username=username, email=email, role='patient')
        user.set_password(password)
        db.session.add(user)
        db.session.flush()
        patient = Patient(
            user_id=user.id,
            full_name=full_name,
            contact_number=contact_number,
            date_of_birth=datetime.strptime(date_of_birth, '%Y-%m-%d').date() if date_of_birth else None,
            gender=gender,
            blood_group=blood_group,
            address=address
        )
        db.session.add(patient)
        db.session.commit()
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

# Register blueprints
app.register_blueprint(admin_bp)
app.register_blueprint(patient_bp)
app.register_blueprint(doctor_bp)

if __name__ == '__main__':
    instance_folder = os.path.join(basedir, 'instance')
    if not os.path.exists(instance_folder):
        os.makedirs(instance_folder)
        print(f"Created instance folder at: {instance_folder}")
    with app.app_context():
        db.create_all()

        if not User.query.filter_by(role='admin').first():
            admin_user = User(username='admin', email='admin@hospital.com', role='admin')
            admin_user.set_password('admin123')
            db.session.add(admin_user)
            db.session.commit()
            print('Admin user created: username=admin, password=admin123')
        else:
            print('Admin user already exists')
        print(f"\nDatabase Statistics:")
        print(f"Total Users: {User.query.count()}")
        print(f"Total Patients: {Patient.query.count()}")
        print(f"Total Doctors: {Doctor.query.count()}")
        print(f"Total Departments: {Department.query.count()}")
        print(f"Total Appointments: {Appointment.query.count()}")
    print(f"\nStarting Flask app...")

    app.run(host='0.0.0.0', port=5000, debug=True)
