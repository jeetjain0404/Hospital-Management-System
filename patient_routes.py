from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Department, Doctor, Patient, Appointment, DoctorAvailability
from datetime import datetime, date, timedelta
from functools import wraps

patient_bp = Blueprint('patient', __name__, url_prefix='/patient')

# Decorator copied from app.py
def patient_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'patient':
            flash('You need patient privileges to access this page.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@patient_bp.route('/dashboard')
@login_required
@patient_required
def patient_dashboard():
    patient = Patient.query.filter_by(user_id=current_user.id).first()
    departments = Department.query.all()
    today = date.today()
    upcoming_appointments = Appointment.query.filter(
        Appointment.patient_id == patient.id,
        Appointment.appointment_date >= today,
        Appointment.status == 'Booked'
    ).order_by(Appointment.appointment_date, Appointment.appointment_time).all()
    past_appointments = Appointment.query.filter(
        Appointment.patient_id == patient.id,
        Appointment.status == 'Completed'
    ).order_by(Appointment.appointment_date.desc()).limit(5).all()
    return render_template('patient/dashboard.html', patient=patient, departments=departments,
        upcoming_appointments=upcoming_appointments, past_appointments=past_appointments)

@patient_bp.route('/doctors')
@login_required
@patient_required
def patient_doctors():
    search_query = request.args.get('search', '')
    department_id = request.args.get('department', '')
    query = Doctor.query
    if search_query:
        query = query.filter(
            (Doctor.full_name.ilike(f'%{search_query}%')) |
            (Doctor.specialization.ilike(f'%{search_query}%'))
        )
    if department_id:
        query = query.filter_by(department_id=int(department_id))
    doctors = query.all()
    departments = Department.query.all()
    today = date.today()
    week_end = today + timedelta(days=7)
    doctor_availability = {}
    for doctor in doctors:
        availability = DoctorAvailability.query.filter(
            DoctorAvailability.doctor_id == doctor.id,
            DoctorAvailability.date >= today,
            DoctorAvailability.date <= week_end,
            DoctorAvailability.is_available == True
        ).order_by(DoctorAvailability.date, DoctorAvailability.start_time).all()
        doctor_availability[doctor.id] = availability
    return render_template('patient/doctors.html', doctors=doctors, departments=departments,
        doctor_availability=doctor_availability, search_query=search_query, selected_department=department_id)

@patient_bp.route('/book/<int:doctor_id>', methods=['GET', 'POST'])
@login_required
@patient_required
def patient_book_appointment(doctor_id):
    doctor = Doctor.query.get_or_404(doctor_id)
    patient = Patient.query.filter_by(user_id=current_user.id).first()
    if request.method == 'POST':
        appointment_date = datetime.strptime(request.form.get('appointment_date'), '%Y-%m-%d').date()
        appointment_time = datetime.strptime(request.form.get('appointment_time'), '%H:%M').time()
        reason = request.form.get('reason')
        existing = Appointment.query.filter_by(
            doctor_id=doctor_id,
            appointment_date=appointment_date,
            appointment_time=appointment_time
        ).filter(Appointment.status != 'Cancelled').first()
        if existing:
            flash('This time slot is already booked. Please choose another time.', 'danger')
            return redirect(url_for('patient.patient_book_appointment', doctor_id=doctor_id))
        appointment = Appointment(
            patient_id=patient.id,
            doctor_id=doctor_id,
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            reason=reason,
            status='Booked'
        )
        db.session.add(appointment)
        db.session.commit()
        flash('Appointment booked successfully!', 'success')
        return redirect(url_for('patient.patient_dashboard'))
    today = date.today()
    week_end = today + timedelta(days=7)
    availabilities = DoctorAvailability.query.filter(
        DoctorAvailability.doctor_id == doctor_id,
        DoctorAvailability.date >= today,
        DoctorAvailability.date <= week_end,
        DoctorAvailability.is_available == True
    ).order_by(DoctorAvailability.date, DoctorAvailability.start_time).all()
    return render_template('patient/book_appointment.html', doctor=doctor, availabilities=availabilities)

@patient_bp.route('/appointments')
@login_required
@patient_required
def patient_appointments():
    patient = Patient.query.filter_by(user_id=current_user.id).first()
    appointments = Appointment.query.filter_by(patient_id=patient.id).order_by(
        Appointment.appointment_date.desc(),
        Appointment.appointment_time.desc()
    ).all()
    return render_template('patient/appointments.html', appointments=appointments)

@patient_bp.route('/appointment/<int:appointment_id>/cancel', methods=['POST'])
@login_required
@patient_required
def patient_cancel_appointment(appointment_id):
    patient = Patient.query.filter_by(user_id=current_user.id).first()
    appointment = Appointment.query.get_or_404(appointment_id)
    if appointment.patient_id != patient.id:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('patient.patient_dashboard'))
    if appointment.status != 'Booked':
        flash('Only booked appointments can be cancelled.', 'warning')
        return redirect(url_for('patient.patient_appointments'))
    appointment.status = 'Cancelled'
    db.session.commit()
    flash('Appointment cancelled successfully!', 'info')
    return redirect(url_for('patient.patient_appointments'))

@patient_bp.route('/profile', methods=['GET', 'POST'])
@login_required
@patient_required
def patient_profile():
    patient = Patient.query.filter_by(user_id=current_user.id).first()
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
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('patient.patient_profile'))
    return render_template('patient/profile.html', patient=patient)

@patient_bp.route('/history')
@login_required
@patient_required
def patient_history():
    patient = Patient.query.filter_by(user_id=current_user.id).first()
    completed_appointments = Appointment.query.filter_by(
        patient_id=patient.id,
        status='Completed'
    ).order_by(Appointment.appointment_date.desc()).all()
    return render_template('patient/history.html', appointments=completed_appointments)
