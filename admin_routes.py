from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, User, Department, Doctor, Patient, Appointment, Treatment, DoctorAvailability
from datetime import datetime, date
from functools import wraps

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Reuse this decorator

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('You need admin privileges to access this page.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/dashboard')
@login_required
@admin_required
def admin_dashboard():
    total_doctors = Doctor.query.count()
    total_patients = Patient.query.count()
    total_appointments = Appointment.query.count()
    upcoming_appointments = Appointment.query.filter(
        Appointment.appointment_date >= date.today(),
        Appointment.status == 'Booked'
    ).count()
    recent_appointments = Appointment.query.order_by(Appointment.created_at.desc()).limit(5).all()
    return render_template('admin/dashboard.html',
        total_doctors=total_doctors,
        total_patients=total_patients,
        total_appointments=total_appointments,
        upcoming_appointments=upcoming_appointments,
        recent_appointments=recent_appointments)

@admin_bp.route('/departments')
@login_required
@admin_required
def admin_departments():
    departments = Department.query.all()
    return render_template('admin/departments.html', departments=departments)

@admin_bp.route('/department/add', methods=['GET','POST'])
@login_required
@admin_required
def admin_add_department():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        if not name:
            flash('Department name is required.', 'danger')
            return redirect(url_for('admin.admin_add_department'))
        if Department.query.filter_by(name=name).first():
            flash('Department already exists.', 'danger')
            return redirect(url_for('admin.admin_add_department'))
        department = Department(name=name, description=description if description else None)
        db.session.add(department)
        db.session.commit()
        flash('Department added successfully!', 'success')
        return redirect(url_for('admin.admin_departments'))
    return render_template('admin/add_department.html')

@admin_bp.route('/department/edit/<int:department_id>', methods=['GET','POST'])
@login_required
@admin_required
def admin_edit_department(department_id):
    department = Department.query.get_or_404(department_id)
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        if not name:
            flash('Department name is required.', 'danger')
            return redirect(url_for('admin.admin_edit_department', department_id=department_id))
        existing = Department.query.filter_by(name=name).first()
        if existing and existing.id != department_id:
            flash('Department name already exists.', 'danger')
            return redirect(url_for('admin.admin_edit_department', department_id=department_id))
        department.name = name
        department.description = description if description else None
        db.session.commit()
        flash('Department updated successfully!', 'success')
        return redirect(url_for('admin.admin_departments'))
    return render_template('admin/edit_department.html', department=department)

@admin_bp.route('/department/delete/<int:department_id>', methods=['POST'])
@login_required
@admin_required
def admin_delete_department(department_id):
    department = Department.query.get_or_404(department_id)
    doctor_count = Doctor.query.filter_by(department_id=department_id).count()
    if doctor_count > 0:
        flash(f'Cannot delete department. {doctor_count} doctor(s) are currently assigned to this department.', 'danger')
        return redirect(url_for('admin.admin_departments'))
    db.session.delete(department)
    db.session.commit()
    flash('Department deleted successfully!', 'success')
    return redirect(url_for('admin.admin_departments'))

@admin_bp.route('/doctors')
@login_required
@admin_required
def admin_doctors():
    search_query = request.args.get('search', '')
    if search_query:
        doctors = Doctor.query.join(User).filter(
            (Doctor.full_name.ilike(f'%{search_query}%')) |
            (Doctor.specialization.ilike(f'%{search_query}%'))
        ).all()
    else:
        doctors = Doctor.query.all()
    return render_template('admin/doctors.html', doctors=doctors, search_query=search_query)

@admin_bp.route('/doctor/add', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_add_doctor():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        full_name = request.form.get('full_name')
        department_id = request.form.get('department_id')
        specialization = request.form.get('specialization')
        qualification = request.form.get('qualification')
        experience_years = request.form.get('experience_years')
        contact_number = request.form.get('contact_number')
        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'danger')
            return redirect(url_for('admin.admin_add_doctor'))
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return redirect(url_for('admin.admin_add_doctor'))
        user = User(username=username, email=email, role='doctor')
        user.set_password(password)
        db.session.add(user)
        db.session.flush()
        doctor = Doctor(
            user_id=user.id,
            full_name=full_name,
            department_id=department_id,
            specialization=specialization,
            qualification=qualification,
            experience_years=int(experience_years) if experience_years else None,
            contact_number=contact_number
        )
        db.session.add(doctor)
        db.session.commit()
        flash('Doctor added successfully!', 'success')
        return redirect(url_for('admin.admin_doctors'))
    departments = Department.query.all()
    return render_template('admin/add_doctor.html', departments=departments)

@admin_bp.route('/doctor/edit/<int:doctor_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_edit_doctor(doctor_id):
    doctor = Doctor.query.get_or_404(doctor_id)
    if request.method == 'POST':
        doctor.full_name = request.form.get('full_name')
        doctor.department_id = request.form.get('department_id')
        doctor.specialization = request.form.get('specialization')
        doctor.qualification = request.form.get('qualification')
        experience = request.form.get('experience_years')
        doctor.experience_years = int(experience) if experience else None
        doctor.contact_number = request.form.get('contact_number')
        db.session.commit()
        flash('Doctor updated successfully!', 'success')
        return redirect(url_for('admin.admin_doctors'))
    departments = Department.query.all()
    return render_template('admin/edit_doctor.html', doctor=doctor, departments=departments)

@admin_bp.route('/doctor/delete/<int:doctor_id>', methods=['POST'])
@login_required
@admin_required
def admin_delete_doctor(doctor_id):
    doctor = Doctor.query.get_or_404(doctor_id)
    user = doctor.user
    # Check for related appointments
    appointment_count = Appointment.query.filter_by(doctor_id=doctor_id).count()
    if appointment_count > 0:
        flash('Doctor has existing appointments and cannot be deleted. Please remove or reassign those appointments first.', 'danger')
        return redirect(url_for('admin.admin_doctors'))
    DoctorAvailability.query.filter_by(doctor_id=doctor_id).delete()
    db.session.delete(doctor)
    db.session.delete(user)
    db.session.commit()
    flash('Doctor deleted successfully!', 'success')
    return redirect(url_for('admin.admin_doctors'))


@admin_bp.route('/patients')
@login_required
@admin_required
def admin_patients():
    search_query = request.args.get('search', '')
    if search_query:
        patients = Patient.query.filter(
            (Patient.full_name.ilike(f'%{search_query}%')) |
            (Patient.contact_number.ilike(f'%{search_query}%'))
        ).all()
    else:
        patients = Patient.query.all()
    return render_template('admin/patients.html', patients=patients, search_query=search_query)

@admin_bp.route('/patient/edit/<int:patient_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_edit_patient(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    if request.method == 'POST':
        patient.full_name = request.form.get('full_name')
        patient.contact_number = request.form.get('contact_number')
        patient.gender = request.form.get('gender')
        patient.blood_group = request.form.get('blood_group')
        patient.address = request.form.get('address')
        patient.emergency_contact = request.form.get('emergency_contact')
        dob = request.form.get('date_of_birth')
        if dob:
            patient.date_of_birth = datetime.strptime(dob, '%Y-%m-%d').date()
        db.session.commit()
        flash('Patient updated successfully!', 'success')
        return redirect(url_for('admin.admin_patients'))
    return render_template('admin/edit_patient.html', patient=patient)

@admin_bp.route('/patient/delete/<int:patient_id>', methods=['POST'])
@login_required
@admin_required
def admin_delete_patient(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    user = patient.user
    user.is_active = False
    db.session.commit()
    flash('Patient blacklisted successfully!', 'success')
    return redirect(url_for('admin.admin_patients'))

@admin_bp.route('/appointments')
@login_required
@admin_required
def admin_appointments():
    appointments = Appointment.query.order_by(Appointment.appointment_date.desc(), Appointment.appointment_time.desc()).all()
    return render_template('admin/appointments.html', appointments=appointments)
