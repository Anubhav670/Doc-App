from flask import * 
from flask import request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import *
from sqlalchemy import exc
from datetime import datetime
import requests
from datetime import time

app= Flask(__name__)



app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///doctors.sqllite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


 
db = SQLAlchemy(app)

class Doctor(db.Model):
	
    __tablename__ = 'Doctor'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    speciality = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    hospitalID = db.Column(db.Integer, db.ForeignKey('Hospital.id'), nullable=False)

    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'speciality': self.speciality,
            'phone': self.phone,
            'hospitalID': self.hospitalID
        }

class Hospital(db.Model):
    __tablename__ = 'Hospital'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(15),unique=True, nullable=False)
    address = db.Column(db.String(200), nullable=False)

class AppointmentSlot(db.Model):
	
    __tablename__ = 'AppointmentSlot'
    id = db.Column(db.Integer, primary_key=True)
    doctorId = db.Column(db.Integer, db.ForeignKey('Doctor.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)

    def serialize(self):
        return {
            'id': self.id,
            'doctorId': self.doctorId,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat()
        }

# Task 1: List all doctors
@app.route('/view-doctors/', methods=['GET'])
def view_doctors():
    doctors = Doctor.query.all()
    doctor_list = []
    for doctor in doctors:
        doctor_info = {
            'id': doctor.id,
            'name': doctor.name,
            'email': doctor.email,
            'speciality': doctor.speciality,
            'phone': doctor.phone,
            'hospitalID':doctor.hospitalID
        }
        doctor_list.append(doctor_info)
    return jsonify(doctor_list)


# Task 2: Delete doctor by id
@app.route('/delete-doctor/<int:id>/', methods=['DELETE'])
def delete_doctor(id):
    doctor = Doctor.query.get(id)
    if doctor:
        # Delete the doctor and associated appointment slots
        db.session.delete(doctor)
        db.session.commit()
        return jsonify({'message': 'Doctor deleted successfully'})
    else:
        return jsonify({'message': 'Doctor not found'}), 404

# Task 3: View doctor details by id
@app.route('/doctor/<int:id>/', methods=['GET'])
def view_doctor(id):
    doctor = Doctor.query.get(id)
    if doctor:
        return jsonify(doctor.serialize())
    else:
        return jsonify({'message': 'Doctor not found'}), 404

# Task 4: Add a new doctor to the database
@app.route('/add-doctor/', methods=['POST'])
def add_doctor():
    data = request.json
    print("hello")
    new_doctor = Doctor(
        name=data['name'],
        email=data['email'],
        speciality=data['speciality'],
        phone=data['phone'],
        hospitalID=data['hospitalID']
    )

    db.session.add(new_doctor)
    print("hello2")
    db.session.commit()
    print("hello3")
    return jsonify({'message': 'Doctor added successfully'})

# Task 5: Get all available slots of the doctor
@app.route('/available-slots/<int:id>/', methods=['GET'])
def available_slots(id):
    doctor = Doctor.query.get(id)
    if doctor:
        appointment_slots = AppointmentSlot.query.filter_by(doctorId=id).all()
        if appointment_slots:
            serialized_slots = [slot.serialize() for slot in appointment_slots]
            return jsonify(serialized_slots)
        else:
            return jsonify({'message': 'All slots for this doctor are Available '}), 404
    else:
        return jsonify({'message': 'Doctor not found'}), 404


# Task 6: Add an appointment slot for the particular doctor
@app.route('/add-appointment/<int:id>/', methods=['POST'])
def add_appointment(id):
    data = request.json
    start_time_str = data.get('start_time')
    end_time_str = data.get('end_time')

    # Convert start_time and end_time strings to datetime objects
    start_time = datetime.strptime(start_time_str, '%Y-%m-%dT%H:%M:%S')
    end_time = datetime.strptime(end_time_str, '%Y-%m-%dT%H:%M:%S')

    # Convert start_time and end_time strings to datetime objects
    start_time1 = datetime.strptime(start_time_str, '%Y-%m-%dT%H:%M:%S').time()
    end_time1 = datetime.strptime(end_time_str, '%Y-%m-%dT%H:%M:%S').time()

    # Check if the appointment slot is valid (between 9 am and 9 pm)
    if start_time1 < time(9, 0) or end_time1 > time(21, 0):
        return jsonify({'message': 'Appointment slot must be between 9 am and 9 pm'}), 400

    # Check if the appointment slot is valid
    if start_time >= end_time:
        return jsonify({'message': 'Invalid appointment slot'}), 400

    # Check if the appointment slot overlaps with existing slots for the doctor
    existing_slots = AppointmentSlot.query.filter(
        AppointmentSlot.doctorId == id,
        (AppointmentSlot.start_time < end_time) & (AppointmentSlot.end_time > start_time)
    ).all()

    if existing_slots:
        return jsonify({'message': 'Appointment slot overlaps with existing slots'}), 400

    # Create a new appointment slot
    new_appointment = AppointmentSlot(
        doctorId=id,
        start_time=start_time,
        end_time=end_time
    )

    db.session.add(new_appointment)
    db.session.commit()
    return jsonify({'message': 'Appointment slot added successfully'})

# Task 7: Delete the particular appointment for the doctor
@app.route('/delete-appointment/<int:id>/', methods=['DELETE'])
def delete_appointment(id):
    appointment = AppointmentSlot.query.get(id)
    if appointment:
        db.session.delete(appointment)
        db.session.commit()
        return jsonify({'message': 'Appointment deleted successfully'})
    else:
        return jsonify({'message': 'Appointment not found'}), 404

# Task 8: Get all appointments for a doctor
@app.route('/doctor/<int:id>/appointments/', methods=['GET'])
def doctor_appointments(id):
    doctor = Doctor.query.get(id)
    if doctor:
        appointments = AppointmentSlot.query.filter_by(doctorId=id).all()
        if appointments:
            serialized_appointments = [appointment.serialize() for appointment in appointments]
            return jsonify(serialized_appointments)
        else:
            return jsonify({'message': 'No appointments found for this doctor'}), 404
    else:
        return jsonify({'message': 'Doctor not found'}), 404

# Task 9: Update an appointment slot for the particular doctor
@app.route('/update-appointment/<int:id>/', methods=['PUT'])
def update_appointment(id):
    data = request.json
    appointment = AppointmentSlot.query.get(id)

    if appointment:
        # Update the appointment slot details
        # Convert start_time and end_time strings to datetime objects
    	start_time1 = datetime.strptime(data['start_time'], '%Y-%m-%dT%H:%M:%S').time()
    	end_time1 = datetime.strptime(data['end_time'], '%Y-%m-%dT%H:%M:%S').time()

    	# Check if the appointment slot is valid (between 9 am and 9 pm)
    	if start_time1 < time(9, 0) or end_time1 > time(21, 0):
    		return jsonify({'message': 'Appointment slot must be between 9 am and 9 pm'}), 400
    	appointment.start_time = datetime.strptime(data['start_time'], '%Y-%m-%dT%H:%M:%S')
    	appointment.end_time = datetime.strptime(data['end_time'], '%Y-%m-%dT%H:%M:%S')
    	db.session.commit()
    	return jsonify({'message': 'Appointment slot updated successfully'})
    else:
        return jsonify({'message': 'Appointment slot not found'}), 404

# Task 10: Get all available slots of a hospital
@app.route('/available-slots/<int:hospital>/', methods=['GET'])
def hospital_available_slots(hospital):
    doctors_in_hospital = Doctor.query.filter_by(hospitalID=hospital).all()
    if doctors_in_hospital:
        available_slots = []
        for doctor in doctors_in_hospital:
            slots = AppointmentSlot.query.filter_by(doctorId=doctor.id).all()
            if slots:
                available_slots.extend(slots)

        if available_slots:
            serialized_slots = [slot.serialize() for slot in available_slots]
            return jsonify(serialized_slots)
        else:
            return jsonify({'message': 'No available slots for doctors in this hospital'}), 404
    else:
        return jsonify({'message': 'No doctors found in this hospital'}), 404

# Task 11: Get all appointments for a hospital
@app.route('/hospital/<int:hospital>/appointments/', methods=['GET'])
def hospital_appointments(hospital):
    doctors_in_hospital = Doctor.query.filter_by(hospitalID=hospital).all()
    if doctors_in_hospital:
        all_appointments = []
        for doctor in doctors_in_hospital:
            appointments = AppointmentSlot.query.filter_by(doctorId=doctor.id).all()
            if appointments:
                all_appointments.extend(appointments)

        if all_appointments:
            serialized_appointments = [appointment.serialize() for appointment in all_appointments]
            return jsonify(serialized_appointments)
        else:
            return jsonify({'message': 'No appointments for doctors in this hospital'}), 404
    else:
        return jsonify({'message': 'No doctors found in this hospital'}), 404


# Task 12: Add a new hospital to the database
@app.route('/add-hospital/', methods=['POST'])
def add_hospital():
    # Implement logic to add a new hospital
    data = request.json
    new_hosp = Hospital(
        name=data['name'],
        phone=data['phone'],
        address=data['address']
    )
    db.session.add(new_hosp)
    db.session.commit()
    return jsonify({'message': 'Hospital added successfully'})

# Task 13: View hospital details by id
@app.route('/hospital/<int:id>/', methods=['GET'])
def view_hospital(id):
    hospital = Hospital.query.get(id)
    if hospital:
        hospital_details = {
            'id': hospital.id,
            'name': hospital.name,
            'phone': hospital.phone,
            'address': hospital.address
        }
        return jsonify(hospital_details)
    else:
        return jsonify({'message': 'Hospital not found'}), 404

# Task 14: View all doctors of a hospital
@app.route('/hospital/<int:hospitalID>/doctors/', methods=['GET'])
def hospital_doctors(hospitalID):
    doctors = Doctor.query.filter_by(hospitalID=hospitalID).all()
    if doctors:
        serialized_doctors = [doctor.serialize() for doctor in doctors]
        return jsonify(serialized_doctors)
    else:
        return jsonify({'message': 'No doctors found for this hospital'}), 404


with app.app_context():
	db.create_all()