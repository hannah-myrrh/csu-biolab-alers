from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
import jwt
from functools import wraps

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///lab_reservation.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key-change-this'

# Configure CORS
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:3000"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

db = SQLAlchemy(app)

# Models
class User(db.Model):
    __tablename__ = 'user'
    userID = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    notifications = db.relationship('Notification', back_populates='user')
    reservations = db.relationship('Reservation', back_populates='user')

class Laboratory(db.Model):
    __tablename__ = 'laboratory'
    labID = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    lab_name = db.Column(db.String(100), unique=True, nullable=False)
    equipment = db.relationship('LabEquipment', back_populates='laboratory')

class LabEquipment(db.Model):
    __tablename__ = 'lab_equipment'
    equipmentID = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    labID = db.Column(db.String(36), db.ForeignKey('laboratory.labID'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='available')
    total_quantity = db.Column(db.Integer, nullable=False, default=1)
    available_quantity = db.Column(db.Integer, nullable=False, default=1)
    laboratory = db.relationship('Laboratory', back_populates='equipment')
    reservations = db.relationship('Reservation', back_populates='equipment')

class Reservation(db.Model):
    __tablename__ = 'reservation'
    reservationID = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    userID = db.Column(db.String(36), db.ForeignKey('user.userID'), nullable=False)
    equipmentID = db.Column(db.String(36), db.ForeignKey('lab_equipment.equipmentID'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')  # pending, approved, rejected, completed, cancelled
    quantity = db.Column(db.Integer, nullable=False, default=1)  # Number of equipment units reserved
    reason = db.Column(db.String(500))  # Student's reason for reservation
    admin_notes = db.Column(db.String(200))  # For admin to provide reason for rejection
    return_timestamp = db.Column(db.DateTime)  # When the equipment was returned
    user = db.relationship('User', back_populates='reservations')
    equipment = db.relationship('LabEquipment', back_populates='reservations')
    notifications = db.relationship('Notification', back_populates='reservation')

class Notification(db.Model):
    __tablename__ = 'notification'
    notificationID = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    userID = db.Column(db.String(36), db.ForeignKey('user.userID'), nullable=False)
    reservationID = db.Column(db.String(36), db.ForeignKey('reservation.reservationID'), nullable=False)
    message = db.Column(db.String(200), nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', back_populates='notifications')
    reservation = db.relationship('Reservation', back_populates='notifications')

# Token required decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        try:
            token = token.split(' ')[1]  # Remove 'Bearer ' prefix
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = User.query.get(data['userID'])
        except:
            return jsonify({'message': 'Token is invalid!'}), 401
        return f(current_user, *args, **kwargs)
    return decorated

# Login route
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'message': 'Missing email or password'}), 400
    
    user = User.query.filter_by(email=data['email']).first()
    
    if not user or not check_password_hash(user.password, data['password']):
        return jsonify({'message': 'Invalid email or password'}), 401
    
    token = jwt.encode({
        'userID': user.userID,
        'email': user.email,
        'role': user.role,
        'exp': datetime.utcnow() + timedelta(days=1)
    }, app.config['SECRET_KEY'])
    
    return jsonify({
        'token': token,
        'user': {
            'userID': user.userID,
            'name': user.name,
            'email': user.email,
            'role': user.role
        }
    })

# Routes

# Frontend route
@app.route('/')
def index():
    return render_template('index.html')

# API Routes

# User Routes
@app.route('/api/users', methods=['GET'])
@token_required
def get_users(current_user):
    if current_user.role != 'admin':
        return jsonify({'message': 'Unauthorized'}), 403
    
    users = User.query.all()
    return jsonify([{
        'userID': user.userID,
        'name': user.name,
        'email': user.email,
        'role': user.role
    } for user in users])

@app.route('/api/users', methods=['POST'])
def create_user():
    data = request.get_json()
    
    # Check if user already exists
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'User with this email already exists'}), 400
    
    hashed_password = generate_password_hash(data['password'])
    
    user = User(
        name=data['name'],
        email=data['email'],
        password=hashed_password,
        role=data['role']
    )
    
    db.session.add(user)
    db.session.commit()
    
    return jsonify({'message': 'User created successfully', 'userID': user.userID}), 201

@app.route('/api/users/<user_id>', methods=['GET'])
def get_user(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify({
        'userID': user.userID,
        'name': user.name,
        'email': user.email,
        'role': user.role
    })

# Laboratory Routes
@app.route('/api/laboratories', methods=['GET'])
def get_laboratories():
    labs = Laboratory.query.all()
    return jsonify([{
        'labID': lab.labID,
        'lab_name': lab.lab_name,
        'equipment_count': len(lab.equipment),
        'equipment': [{
            'equipmentID': eq.equipmentID,
            'name': eq.name,
            'status': eq.status,
            'total_quantity': eq.total_quantity,
            'available_quantity': eq.available_quantity
        } for eq in lab.equipment]
    } for lab in labs])

@app.route('/api/laboratories', methods=['POST'])
@token_required
def create_laboratory(current_user):
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    
    if not data or 'lab_name' not in data:
        return jsonify({'error': 'Missing laboratory name'}), 400
    
    try:
        lab = Laboratory(lab_name=data['lab_name'])
        db.session.add(lab)
        db.session.commit()
        
        return jsonify({
            'message': 'Laboratory created successfully',
            'laboratory': {
                'labID': lab.labID,
                'lab_name': lab.lab_name,
                'equipment_count': 0
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create laboratory'}), 500

@app.route('/api/laboratories/<lab_id>', methods=['DELETE'])
def delete_laboratory(lab_id):
    lab = Laboratory.query.get_or_404(lab_id)
    db.session.delete(lab)
    db.session.commit()
    return jsonify({'message': 'Laboratory deleted successfully'})

# Lab Equipment Routes
@app.route('/api/equipment', methods=['GET'])
def get_equipment():
    equipment = LabEquipment.query.all()
    return jsonify([{
        'equipmentID': eq.equipmentID,
        'name': eq.name,
        'labID': eq.labID,
        'lab_name': eq.laboratory.lab_name,
        'status': eq.status,
        'total_quantity': eq.total_quantity,
        'available_quantity': eq.available_quantity
    } for eq in equipment])

@app.route('/api/equipment', methods=['POST'])
@token_required
def create_equipment(current_user):
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['name', 'labID', 'total_quantity']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    # Validate laboratory exists
    lab = Laboratory.query.get(data['labID'])
    if not lab:
        return jsonify({'error': 'Laboratory not found'}), 400
    
    # Validate total quantity
    if data['total_quantity'] < 1:
        return jsonify({'error': 'Total quantity must be at least 1'}), 400
    
    try:
        equipment = LabEquipment(
            name=data['name'],
            labID=data['labID'],
            total_quantity=data['total_quantity'],
            available_quantity=data['total_quantity'],
            status='available'
        )
        
        db.session.add(equipment)
        db.session.commit()
        
        return jsonify({
            'message': 'Equipment created successfully',
            'equipment': {
                'equipmentID': equipment.equipmentID,
                'name': equipment.name,
                'labID': equipment.labID,
                'lab_name': lab.lab_name,
                'status': equipment.status,
                'total_quantity': equipment.total_quantity,
                'available_quantity': equipment.available_quantity
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create equipment'}), 500

@app.route('/api/equipment/<equipment_id>', methods=['PUT'])
def update_equipment_status(equipment_id):
    equipment = LabEquipment.query.get_or_404(equipment_id)
    data = request.get_json()
    
    equipment.status = data['status']
    db.session.commit()
    
    return jsonify({'message': 'Equipment status updated successfully'})

@app.route('/api/equipment/<equipment_id>', methods=['DELETE'])
def delete_equipment(equipment_id):
    equipment = LabEquipment.query.get_or_404(equipment_id)
    db.session.delete(equipment)
    db.session.commit()
    return jsonify({'message': 'Equipment deleted successfully'})

# Reservation Routes
@app.route('/api/reservations', methods=['GET'])
def get_reservations():
    reservations = Reservation.query.all()
    return jsonify([{
        'reservationID': res.reservationID,
        'userID': res.userID,
        'equipmentID': res.equipmentID,
        'start_time': res.start_time.isoformat(),
        'end_time': res.end_time.isoformat(),
        'status': res.status,
        'quantity': res.quantity,
        'reason': res.reason,
        'admin_notes': res.admin_notes,
        'return_timestamp': res.return_timestamp.isoformat() if res.return_timestamp else None,
        'user_name': res.user.name if res.user else 'Unknown User',
        'equipment_name': res.equipment.name if res.equipment else 'Unknown Equipment'
    } for res in reservations])

@app.route('/api/reservations', methods=['POST'])
def create_reservation():
    data = request.get_json()
    print("Received reservation data:", data)
    
    # Validate required fields
    required_fields = ['userID', 'equipmentID', 'start_time', 'end_time', 'reason', 'quantity']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    try:
        # Parse datetime strings
        start_time = datetime.fromisoformat(data['start_time'].replace('Z', '+00:00'))
        end_time = datetime.fromisoformat(data['end_time'].replace('Z', '+00:00'))
        
        # Get equipment and check availability
        equipment = LabEquipment.query.get(data['equipmentID'])
        if not equipment:
            return jsonify({'error': 'Equipment not found'}), 400
        
        quantity = int(data['quantity'])
        if quantity <= 0:
            return jsonify({'error': 'Quantity must be greater than 0'}), 400
        
        if equipment.available_quantity < quantity:
            return jsonify({'error': f'Only {equipment.available_quantity} units available'}), 400
        
        # Check for conflicting reservations
        conflicts = Reservation.query.filter(
            Reservation.equipmentID == data['equipmentID'],
            Reservation.status.in_(['pending', 'approved']),
            ((Reservation.start_time <= start_time) & (Reservation.end_time > start_time)) |
            ((Reservation.start_time < end_time) & (Reservation.end_time >= end_time)) |
            ((Reservation.start_time >= start_time) & (Reservation.end_time <= end_time))
        ).count()
        
        if conflicts >= equipment.available_quantity:
            return jsonify({'error': 'No available units during the requested time slot'}), 400
        
        # Create new reservation
        reservation = Reservation(
            userID=data['userID'],
            equipmentID=data['equipmentID'],
            start_time=start_time,
            end_time=end_time,
            status='pending',
            reason=data['reason'],
            quantity=quantity
        )
        
        db.session.add(reservation)
        db.session.flush()
        
        # Create notification
        notification = Notification(
            userID=data['userID'],
            reservationID=reservation.reservationID,
            message=f'Your reservation for {quantity} {equipment.name}(s) has been created and is pending approval.',
            is_read=False
        )
        
        db.session.add(notification)
        db.session.commit()
        
        return jsonify({'message': 'Reservation created successfully', 'reservationID': reservation.reservationID}), 201
        
    except ValueError as e:
        return jsonify({'error': f'Invalid date format: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        print(f"Error creating reservation: {str(e)}")
        return jsonify({'error': 'Failed to create reservation'}), 500

@app.route('/api/reservations/<reservation_id>/status', methods=['PUT'])
@token_required
def update_reservation_status(current_user, reservation_id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    if 'status' not in data or data['status'] not in ['approved', 'rejected', 'returned']:
        return jsonify({'error': 'Invalid status'}), 400
    
    reservation = Reservation.query.get(reservation_id)
    if not reservation:
        return jsonify({'error': 'Reservation not found'}), 404
    
    if reservation.status != 'pending' and data['status'] == 'returned' and reservation.status != 'approved':
        return jsonify({'error': 'Can only mark approved reservations as returned'}), 400
    
    if reservation.status != 'pending' and data['status'] in ['approved', 'rejected']:
        return jsonify({'error': 'Can only update pending reservations'}), 400
    
    try:
        old_status = reservation.status
        reservation.status = data['status']
        reservation.admin_notes = data.get('admin_notes', '')
        
        # Set return timestamp if status is returned
        if data['status'] == 'returned':
            reservation.return_timestamp = datetime.utcnow()
        
        # Update equipment availability if approved
        if data['status'] == 'approved':
            equipment = LabEquipment.query.get(reservation.equipmentID)
            if equipment.available_quantity < reservation.quantity:
                return jsonify({'error': f'Only {equipment.available_quantity} units available'}), 400
            equipment.available_quantity -= reservation.quantity
        # Return equipment to available quantity if returned
        elif data['status'] == 'returned':
            equipment = LabEquipment.query.get(reservation.equipmentID)
            equipment.available_quantity += reservation.quantity
        
        # Create notification
        status_message = data['status']
        notification_message = f'Your reservation for {reservation.quantity} {reservation.equipment.name}(s) has been {status_message}.'
        if data['status'] == 'returned':
            notification_message += f' Equipment was returned on {reservation.return_timestamp.strftime("%Y-%m-%d %H:%M:%S")}.'
        if reservation.admin_notes:
            notification_message += f' {reservation.admin_notes}'
            
        notification = Notification(
            userID=reservation.userID,
            reservationID=reservation.reservationID,
            message=notification_message,
            is_read=False
        )
        
        db.session.add(notification)
        db.session.commit()
        
        return jsonify({
            'message': f'Reservation {status_message} successfully',
            'return_timestamp': reservation.return_timestamp.isoformat() if reservation.return_timestamp else None,
            'admin_notes': reservation.admin_notes
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update reservation status'}), 500

@app.route('/api/reservations/<reservation_id>/complete', methods=['PUT'])
@token_required
def complete_reservation(current_user, reservation_id):
    reservation = Reservation.query.get(reservation_id)
    if not reservation:
        return jsonify({'error': 'Reservation not found'}), 404
    
    # Only allow the user who made the reservation or an admin to complete it
    if current_user.userID != reservation.userID and current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    if reservation.status != 'approved':
        return jsonify({'error': 'Can only complete approved reservations'}), 400
    
    try:
        reservation.status = 'completed'
        
        # Return equipment to available quantity
        equipment = LabEquipment.query.get(reservation.equipmentID)
        equipment.available_quantity += 1
        
        db.session.commit()
        return jsonify({'message': 'Reservation completed successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to complete reservation'}), 500

@app.route('/api/users/<user_id>/reservations', methods=['GET'])
def get_user_reservations(user_id):
    reservations = Reservation.query.filter_by(userID=user_id).all()
    return jsonify([{
        'reservationID': res.reservationID,
        'equipmentID': res.equipmentID,
        'start_time': res.start_time.isoformat(),
        'end_time': res.end_time.isoformat(),
        'status': res.status,
        'quantity': res.quantity,
        'reason': res.reason,
        'admin_notes': res.admin_notes,
        'return_timestamp': res.return_timestamp.isoformat() if res.return_timestamp else None,
        'equipment_name': res.equipment.name,
        'laboratory_name': res.equipment.laboratory.lab_name
    } for res in reservations])

# Notification Routes
@app.route('/api/notifications/<user_id>', methods=['GET'])
def get_user_notifications(user_id):
    notifications = Notification.query.filter_by(userID=user_id).order_by(Notification.created_at.desc()).all()
    return jsonify([{
        'notificationID': notif.notificationID,
        'message': notif.message,
        'timestamp': notif.created_at.isoformat(),
        'reservationID': notif.reservationID
    } for notif in notifications])

# Equipment availability check
@app.route('/api/equipment/<equipment_id>/availability', methods=['GET'])
def check_equipment_availability(equipment_id):
    start_time = request.args.get('start_time')
    end_time = request.args.get('end_time')
    
    if not start_time or not end_time:
        return jsonify({'error': 'start_time and end_time parameters are required'}), 400
    
    start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
    end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
    
    conflicting_reservations = Reservation.query.filter(
        Reservation.equipmentID == equipment_id,
        Reservation.status.in_(['confirmed', 'pending']),
        Reservation.start_time < end_dt,
        Reservation.end_time > start_dt
    ).all()
    
    return jsonify({
        'available': len(conflicting_reservations) == 0,
        'conflicting_reservations': len(conflicting_reservations)
    })

# Initialize database function
def init_db():
    with app.app_context():
        # Drop all tables first to ensure clean state
        db.drop_all()
        db.create_all()
        
        # Create initial laboratories
        labs = [
            Laboratory(lab_name='Computer Science Lab'),
            Laboratory(lab_name='Electronics Lab'),
            Laboratory(lab_name='Robotics Lab'),
            Laboratory(lab_name='Networking Lab')
        ]
        
        db.session.add_all(labs)
        db.session.commit()

# Run the initialization
if __name__ == '__main__':
    init_db()
    app.run(debug=True)