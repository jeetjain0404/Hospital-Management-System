# Hospital Management System

## Overview
A comprehensive web-based Hospital Management System built with Flask, SQLAlchemy, and Bootstrap. The system provides role-based access control for three types of users: Admins, Doctors, and Patients, enabling efficient management of appointments, medical records, and hospital operations.

## Project Purpose
This application helps hospitals manage patient records, doctor schedules, appointments, and treatment histories in a centralized, secure platform. It eliminates manual record-keeping and reduces scheduling conflicts while providing patients with easy access to their medical information.

## Tech Stack
**Backend:**
- Flask 3.1.2 (Web Framework)
- Flask-SQLAlchemy 3.1.1 (ORM)
- Flask-Login 0.6.3 (Authentication)
- Flask-WTF 1.2.2 (CSRF Protection)
- SQLite (Database)
- Werkzeug (Password Hashing)

**Frontend:**
- Jinja2 (Templating)
- Bootstrap 5.3 (UI Framework)
- Font Awesome 6.4 (Icons)
- HTML5 & CSS3
- JavaScript (Form Validation)

## Database Schema
The application uses SQLite with the following models:
- **User**: Base user model with role-based authentication (admin/doctor/patient)
- **Department**: Medical departments/specializations
- **Doctor**: Doctor profiles linked to departments and users
- **Patient**: Patient profiles with medical information
- **Appointment**: Scheduled consultations with conflict prevention
- **Treatment**: Medical records for completed appointments
- **DoctorAvailability**: Doctor schedules for the next 7 days

## Key Features

### Admin Features
- Dashboard with statistics (total doctors, patients, appointments)
- Full CRUD operations for doctors and patients
- Department management
- Search functionality for doctors and patients
- View and manage all appointments
- Blacklist/deactivate users

### Doctor Features
- Personal dashboard with upcoming appointments
- View assigned patients
- Manage availability for next 7 days
- Complete appointments with diagnosis and prescriptions
- View patient medical history
- Cancel appointments

### Patient Features
- Self-registration and login
- Search doctors by name/specialization/department
- View doctor availability for next 7 days
- Book appointments with conflict prevention
- Cancel booked appointments
- View appointment history
- Access treatment records and prescriptions
- Update personal profile

## Security Features
- Password hashing using Werkzeug
- Session-based authentication with Flask-Login
- Role-based access control with decorators
- CSRF protection via Flask-WTF on all POST forms
- Active/inactive user status management

### CSRF Protection Implementation
All POST forms in this application use manual CSRF protection via hidden input fields. When creating new POST forms, always include:

```html
<form method="POST" action="{{ url_for('route_name') }}">
    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
    <!-- rest of form fields -->
</form>
```

**Important:** The CSRF token must be included as a hidden input field. Simply calling `{{ csrf_token() }}` without wrapping it in an input tag will NOT work. CSRFProtect is initialized in `app.py` and validates all POST requests automatically.

## Default Credentials
**Admin Account** (created automatically on first run):
- Username: `admin`
- Password: `admin123`
- Email: admin@hospital.com


## Recent Changes
**2025-11-01**: Template System and CSRF Security Fix
- Created complete template directory structure with 21+ HTML files:
  - Base templates: base.html, index.html, login.html, register.html
  - Admin templates: dashboard, departments, doctors, patients, appointments (with add/edit forms)
  - Doctor templates: dashboard, appointments, availability, complete_appointment, patient_history
  - Patient templates: dashboard, doctors, book_appointment, appointments, profile, history
- Fixed critical CSRF security issue by adding proper hidden input fields to all POST forms
- Implemented correct CSRF protection: `<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">`
- Created setup_sample_data.py script to populate database with test data (5 departments, 3 doctors, 3 patients, 3 appointments)
- Fixed appointment booking functionality with proper form validation and CSRF compliance
- Fixed admin dashboard patient and doctor list views
- All templates use Bootstrap 5.3 for consistent, responsive design
- Verified all POST flows (login, registration, booking, admin CRUD) work correctly with CSRF validation

**2025-10-31**: Department Database Fix
- Fixed Department model schema: changed `name` field from `nullable=True` to `nullable=False`
- Added proper validation for department name (required field, no empty strings)
- Implemented department edit route with name uniqueness validation
- Implemented department delete route with cascade protection (prevents deletion if doctors assigned)
- Created edit_department.html template for editing departments
- Updated departments.html template to include Edit and Delete action buttons
- Created database migration script (migrate_db.py) to handle NULL department names safely
- Verified all department CRUD operations work correctly

**2025-10-28**: Initial project creation and completion
- Created complete Flask application structure
- Implemented all database models with SQLAlchemy
- Built authentication system with Flask-Login and role-based access control
- Added CSRF protection via Flask-WTF on all POST forms
- Created all routes for Admin, Doctor, and Patient roles
- Designed responsive UI with Bootstrap 5
- Added form validation (HTML5 and backend)
- Implemented appointment conflict prevention with unique constraints
- Set up workflow for development server on port 5000
- Auto-created admin user on database initialization
- Passed comprehensive security and functionality review

## Application Flow
1. **Landing Page**: Users can login or register (patients only)
2. **Admin**: Manages system, adds doctors, views all data
3. **Doctor**: Views appointments, sets availability, completes treatments
4. **Patient**: Books appointments, views history, manages profile

## Core Functionalities Implemented
✅ Programmatic database creation with SQLAlchemy 

✅ Auto-creation of admin user

✅ Role-based authentication and authorization

✅ Appointment conflict prevention (unique constraint)

✅ Appointment status tracking (Booked → Completed/Cancelled)

✅ Doctor availability management (7-day rolling window)

✅ Treatment record storage with diagnosis & prescriptions

✅ Search functionality for doctors and patients

✅ HTML5 form validation

✅ Backend validation in routes

✅ Responsive Bootstrap UI

✅ Flash messages for user feedback



## Database Notes
- Database is created programmatically via `db.create_all()` in app.py
- Admin user is automatically created if not exists
- All relationships use proper foreign keys and cascading deletes
- Unique constraints prevent appointment conflicts
