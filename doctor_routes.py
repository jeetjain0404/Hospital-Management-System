from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Doctor, Patient, Appointment, Treatment, DoctorAvailability
from datetime import datetime, date, timedelta
from functools import wraps

doctor_bp = Blueprint('doctor', __name__, url_prefix='/doctor')

# Decorator for doctor role checking

def doctor_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'doctor':
            flash('You need doctor privileges to access this page.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@doctor_bp.route('/dashboard')
@login_required
@doctor_required
def doctor_dashboard():
    doctor = Doctor.query.filter_by(user_id=current_user.id).first()
    today = date.today()
    week_end = today + timedelta(days=7)
    upcoming_appointments = Appointment.query.filter(
        Appointment.doctor_id == doctor.id,
        Appointment.appointment_date >= today,
        Appointment.appointment_date <= week_end,
        Appointment.status == 'Booked'
    ).order_by(Appointment.appointment_date, Appointment.appointment_time).all()
    unique_patients = db.session.query(Patient).join(Appointment).filter(
        Appointment.doctor_id == doctor.id).distinct().all()
    return render_template('doctor/dashboard.html', doctor=doctor,
                          upcoming_appointments=upcoming_appointments,
                          patients=unique_patients)

@doctor_bp.route('/appointments')
@login_required
@doctor_required
def doctor_appointments():
    doctor = Doctor.query.filter_by(user_id=current_user.id).first()
    appointments = Appointment.query.filter_by(doctor_id=doctor.id).order_by(
        Appointment.appointment_date.desc(),
        Appointment.appointment_time.desc()
    ).all()
    return render_template('doctor/appointments.html', appointments=appointments)

@doctor_bp.route('/appointment/<int:appointment_id>/complete', methods=['GET', 'POST'])
@login_required
@doctor_required
def doctor_complete_appointment(appointment_id):
    doctor = Doctor.query.filter_by(user_id=current_user.id).first()
    appointment = Appointment.query.get_or_404(appointment_id)
    if appointment.doctor_id != doctor.id:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('doctor.doctor_dashboard'))
    if request.method == 'POST':
        diagnosis = request.form.get('diagnosis')
        prescription = request.form.get('prescription')
        notes = request.form.get('notes')
        appointment.status = 'Completed'
        if appointment.treatment:
            appointment.treatment.diagnosis = diagnosis
            appointment.treatment.prescription = prescription
            appointment.treatment.notes = notes
        else:
            treatment = Treatment(
                appointment_id=appointment.id,
                diagnosis=diagnosis,
                prescription=prescription,
                notes=notes
            )
            db.session.add(treatment)
        db.session.commit()
        flash('Appointment marked as completed!', 'success')
        return redirect(url_for('doctor.doctor_appointments'))
    return render_template('doctor/complete_appointment.html', appointment=appointment)

@doctor_bp.route('/appointment/<int:appointment_id>/cancel', methods=['POST'])
@login_required
@doctor_required
def doctor_cancel_appointment(appointment_id):
    doctor = Doctor.query.filter_by(user_id=current_user.id).first()
    appointment = Appointment.query.get_or_404(appointment_id)
    if appointment.doctor_id != doctor.id:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('doctor.doctor_dashboard'))
    appointment.status = 'Cancelled'
    db.session.commit()
    flash('Appointment cancelled.', 'info')
    return redirect(url_for('doctor.doctor_appointments'))

@doctor_bp.route('/patient/<int:patient_id>/history')
@login_required
@doctor_required
def doctor_patient_history(patient_id):
    doctor = Doctor.query.filter_by(user_id=current_user.id).first()
    patient = Patient.query.get_or_404(patient_id)
    appointments = Appointment.query.filter_by(
        patient_id=patient_id,
        doctor_id=doctor.id,
        status='Completed'
    ).order_by(Appointment.appointment_date.desc()).all()
    return render_template('doctor/patient_history.html', patient=patient, appointments=appointments)

@doctor_bp.route('/availability', methods=['GET','POST'])
@login_required
@doctor_required
def doctor_availability():
    doctor = Doctor.query.filter_by(user_id=current_user.id).first()
    if request.method == 'POST':
        date_str = request.form.get('date')
        start_time_str = request.form.get('start_time')
        end_time_str = request.form.get('end_time')
        avail_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        start_time_obj = datetime.strptime(start_time_str, '%H:%M').time()
        end_time_obj = datetime.strptime(end_time_str, '%H:%M').time()
        existing = DoctorAvailability.query.filter_by(
            doctor_id=doctor.id,
            date=avail_date,
            start_time=start_time_obj
        ).first()
        if existing:
            flash('Availability already exists for this time slot.', 'warning')
        else:
            availability = DoctorAvailability(
                doctor_id=doctor.id,
                date=avail_date,
                start_time=start_time_obj,
                end_time=end_time_obj
            )
            db.session.add(availability)
            db.session.commit()
            flash('Availability added successfully!', 'success')
        return redirect(url_for('doctor.doctor_availability'))
    today = date.today()
    week_end = today + timedelta(days=7)
    availabilities = DoctorAvailability.query.filter(
        DoctorAvailability.doctor_id == doctor.id,
        DoctorAvailability.date >= today,
        DoctorAvailability.date <= week_end
    ).order_by(DoctorAvailability.date, DoctorAvailability.start_time).all()
    return render_template('doctor/availability.html', availabilities=availabilities)
