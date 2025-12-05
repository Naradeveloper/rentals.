from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os
from datetime import datetime, timedelta
import stripe
import folium
import json
from sqlalchemy import or_, and_

app = Flask(__name__)
app.config.from_object('config.Config')

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
stripe.api_key = app.config['STRIPE_SECRET_KEY']

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_admin = db.Column(db.Boolean, default=False)

class Property(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    property_type = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float, nullable=False)
    deposit = db.Column(db.Float, nullable=False)
    size = db.Column(db.String(50))
    location = db.Column(db.String(200), nullable=False)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    address = db.Column(db.Text)
    bedrooms = db.Column(db.Integer)
    bathrooms = db.Column(db.Integer)
    amenities = db.Column(db.Text)
    video_url = db.Column(db.String(500))
    images = db.Column(db.Text)
    is_available = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Virtual tour fields
    virtual_tour_url = db.Column(db.String(500))
    virtual_tour_type = db.Column(db.String(50))  # video, 360, youtube
    
    # Booking status
    is_booked = db.Column(db.Boolean, default=False)
    booked_until = db.Column(db.DateTime)

class Inquiry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    message = db.Column(db.Text)
    contact_preference = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50), default='pending')  # pending, contacted, closed

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'))
    booking_date = db.Column(db.DateTime, default=datetime.utcnow)
    check_in_date = db.Column(db.DateTime)
    check_out_date = db.Column(db.DateTime)
    status = db.Column(db.String(50), default='pending')  # pending, confirmed, cancelled, completed
    deposit_paid = db.Column(db.Boolean, default=False)
    total_amount = db.Column(db.Float)
    special_requests = db.Column(db.Text)
    
    # Relationships
    property = db.relationship('Property', backref='bookings')
    user = db.relationship('User', backref='bookings')

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'))
    booking_id = db.Column(db.Integer, db.ForeignKey('booking.id'))
    amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(50))
    stripe_payment_id = db.Column(db.String(100))
    status = db.Column(db.String(50), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    transaction_type = db.Column(db.String(50))  # deposit, rent, full_payment

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Admin decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Admin access required', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# ========== MAIN ROUTES ==========

@app.route('/')
def index():
    categories = [
        {'type': 'bedsitter', 'name': 'Bedsitters', 'icon': 'bed', 'count': Property.query.filter_by(property_type='bedsitter', is_available=True, is_booked=False).count()},
        {'type': 'single_room', 'name': 'Single Rooms', 'icon': 'door-closed', 'count': Property.query.filter_by(property_type='single_room', is_available=True, is_booked=False).count()},
        {'type': 'one_bedroom', 'name': 'One Bedrooms', 'icon': 'door-open', 'count': Property.query.filter_by(property_type='one_bedroom', is_available=True, is_booked=False).count()},
        {'type': 'two_bedroom', 'name': 'Two Bedrooms', 'icon': 'building', 'count': Property.query.filter_by(property_type='two_bedroom', is_available=True, is_booked=False).count()}
    ]
    
    featured_properties = Property.query.filter_by(is_available=True, is_booked=False).limit(6).all()
    
    # Create map
    map_center = [-1.286389, 36.817223]
    property_map = folium.Map(location=map_center, zoom_start=12)
    
    for prop in Property.query.filter_by(is_available=True, is_booked=False).all():
        if prop.latitude and prop.longitude:
            folium.Marker(
                [prop.latitude, prop.longitude],
                popup=f"<b>{prop.title}</b><br>KES {prop.price:,.0f}/month<br><a href='/property/{prop.id}'>View Details</a>",
                icon=folium.Icon(color='red', icon='home')
            ).add_to(property_map)
    
    map_html = property_map._repr_html_() if property_map else ''
    
    return render_template('index.html', 
                         categories=categories, 
                         featured_properties=featured_properties,
                         map_html=map_html)

# ========== ADVANCED SEARCH & FILTERING ==========

@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        location = request.form.get('location', '').strip()
        property_type = request.form.get('property_type', '')
        min_price = request.form.get('min_price', type=float)
        max_price = request.form.get('max_price', type=float)
        bedrooms = request.form.get('bedrooms', type=int)
        
        # Build query
        query = Property.query.filter_by(is_available=True, is_booked=False)
        
        if location:
            query = query.filter(Property.location.ilike(f'%{location}%'))
        
        if property_type and property_type != 'all':
            query = query.filter_by(property_type=property_type)
        
        if min_price:
            query = query.filter(Property.price >= min_price)
        
        if max_price:
            query = query.filter(Property.price <= max_price)
        
        if bedrooms is not None:
            query = query.filter(Property.bedrooms == bedrooms)
        
        # Amenities filter
        amenities = request.form.getlist('amenities')
        if amenities:
            for amenity in amenities:
                query = query.filter(Property.amenities.ilike(f'%{amenity}%'))
        
        properties = query.all()
        
        return render_template('search_results.html', 
                             properties=properties,
                             search_params=request.form)
    
    return render_template('search.html')

# ========== PROPERTY & BOOKING ROUTES ==========

@app.route('/property/<int:property_id>')
def property_detail(property_id):
    property = Property.query.get_or_404(property_id)
    
    amenities = json.loads(property.amenities) if property.amenities else []
    images = json.loads(property.images) if property.images else []
    
    # Check if user has already booked this property
    user_booking = None
    if current_user.is_authenticated:
        user_booking = Booking.query.filter_by(
            user_id=current_user.id,
            property_id=property_id,
            status='confirmed'
        ).first()
    
    return render_template('property.html', 
                         property=property,
                         amenities=amenities,
                         images=images,
                         user_booking=user_booking)

@app.route('/property/<int:property_id>/virtual-tour')
def virtual_tour(property_id):
    property = Property.query.get_or_404(property_id)
    
    if not property.virtual_tour_url:
        flash('No virtual tour available for this property', 'warning')
        return redirect(url_for('property_detail', property_id=property_id))
    
    return render_template('virtual_tour.html', property=property)

@app.route('/property/<int:property_id>/book', methods=['GET', 'POST'])
@login_required
def book_property(property_id):
    property = Property.query.get_or_404(property_id)
    
    if property.is_booked:
        flash('This property is already booked', 'error')
        return redirect(url_for('property_detail', property_id=property_id))
    
    if request.method == 'POST':
        check_in = request.form.get('check_in')
        check_out = request.form.get('check_out')
        special_requests = request.form.get('special_requests', '')
        
        # Create booking
        booking = Booking(
            user_id=current_user.id,
            property_id=property_id,
            check_in_date=datetime.strptime(check_in, '%Y-%m-%d') if check_in else None,
            check_out_date=datetime.strptime(check_out, '%Y-%m-%d') if check_out else None,
            special_requests=special_requests,
            total_amount=property.deposit,
            status='pending'
        )
        
        db.session.add(booking)
        db.session.commit()
        
        flash('Booking request submitted! Please pay deposit to confirm.', 'success')
        return redirect(url_for('payment_options', booking_id=booking.id))
    
    return render_template('booking_form.html', property=property)

@app.route('/booking/<int:booking_id>/payment-options')
@login_required
def payment_options(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    
    if booking.user_id != current_user.id and not current_user.is_admin:
        flash('Unauthorized access', 'error')
        return redirect(url_for('index'))
    
    return render_template('payment_options.html', booking=booking)

@app.route('/booking/<int:booking_id>/pay-deposit')
@login_required
def pay_deposit(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    property = Property.query.get(booking.property_id)
    
    if booking.user_id != current_user.id:
        flash('Unauthorized access', 'error')
        return redirect(url_for('index'))
    
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'kes',
                    'product_data': {
                        'name': f'Deposit for {property.title}',
                        'description': f'Booking #{booking_id}',
                    },
                    'unit_amount': int(property.deposit * 100),
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=url_for('payment_success', booking_id=booking_id, _external=True),
            cancel_url=url_for('payment_options', booking_id=booking_id, _external=True),
            metadata={
                'booking_id': booking_id,
                'user_id': current_user.id,
                'property_id': property.id
            }
        )
        
        return redirect(checkout_session.url)
        
    except Exception as e:
        flash(f'Error creating payment session: {str(e)}', 'error')
        return redirect(url_for('payment_options', booking_id=booking_id))

@app.route('/payment/success/<int:booking_id>')
@login_required
def payment_success(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    property = Property.query.get(booking.property_id)
    
    # Update booking status
    booking.status = 'confirmed'
    booking.deposit_paid = True
    db.session.commit()
    
    # Update property status
    property.is_booked = True
    property.booked_until = booking.check_out_date
    db.session.commit()
    
    # Create payment record
    payment = Payment(
        user_id=current_user.id,
        property_id=property.id,
        booking_id=booking_id,
        amount=property.deposit,
        payment_method='stripe',
        status='completed',
        transaction_type='deposit'
    )
    db.session.add(payment)
    db.session.commit()
    
    flash('Payment successful! Your booking is now confirmed.', 'success')
    return render_template('booking_success.html', booking=booking, property=property)

# ========== ADMIN PANEL ROUTES ==========

@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    # Statistics
    total_properties = Property.query.count()
    available_properties = Property.query.filter_by(is_available=True, is_booked=False).count()
    total_bookings = Booking.query.count()
    pending_bookings = Booking.query.filter_by(status='pending').count()
    total_users = User.query.count()
    total_revenue = db.session.query(db.func.sum(Payment.amount)).filter(Payment.status == 'completed').scalar() or 0
    
    # Recent bookings
    recent_bookings = Booking.query.order_by(Booking.booking_date.desc()).limit(10).all()
    
    # Recent payments
    recent_payments = Payment.query.order_by(Payment.created_at.desc()).limit(10).all()
    
    return render_template('admin/dashboard.html',
                         total_properties=total_properties,
                         available_properties=available_properties,
                         total_bookings=total_bookings,
                         pending_bookings=pending_bookings,
                         total_users=total_users,
                         total_revenue=total_revenue,
                         recent_bookings=recent_bookings,
                         recent_payments=recent_payments)

@app.route('/admin/properties')
@login_required
@admin_required
def admin_properties():
    properties = Property.query.all()
    return render_template('admin/properties.html', properties=properties)

@app.route('/admin/properties/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_property():
    if request.method == 'POST':
        try:
            # Get form data
            title = request.form.get('title')
            description = request.form.get('description')
            property_type = request.form.get('property_type')
            price = float(request.form.get('price'))
            deposit = float(request.form.get('deposit'))
            size = request.form.get('size')
            location = request.form.get('location')
            address = request.form.get('address')
            bedrooms = int(request.form.get('bedrooms', 0))
            bathrooms = int(request.form.get('bathrooms', 0))
            amenities = json.dumps(request.form.getlist('amenities'))
            video_url = request.form.get('video_url')
            virtual_tour_url = request.form.get('virtual_tour_url')
            virtual_tour_type = request.form.get('virtual_tour_type')
            
            # Create property
            property = Property(
                title=title,
                description=description,
                property_type=property_type,
                price=price,
                deposit=deposit,
                size=size,
                location=location,
                address=address,
                bedrooms=bedrooms,
                bathrooms=bathrooms,
                amenities=amenities,
                video_url=video_url,
                virtual_tour_url=virtual_tour_url,
                virtual_tour_type=virtual_tour_type,
                images=json.dumps(['/static/images/house-placeholder.jpg']),
                owner_id=current_user.id
            )
            
            db.session.add(property)
            db.session.commit()
            
            flash('Property added successfully!', 'success')
            return redirect(url_for('admin_properties'))
            
        except Exception as e:
            flash(f'Error adding property: {str(e)}', 'error')
    
    return render_template('admin/add_property.html')

@app.route('/admin/bookings')
@login_required
@admin_required
def admin_bookings():
    bookings = Booking.query.order_by(Booking.booking_date.desc()).all()
    return render_template('admin/bookings.html', bookings=bookings)

@app.route('/admin/bookings/<int:booking_id>/update', methods=['POST'])
@login_required
@admin_required
def update_booking_status(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    new_status = request.form.get('status')
    
    if new_status in ['pending', 'confirmed', 'cancelled', 'completed']:
        booking.status = new_status
        db.session.commit()
        flash('Booking status updated successfully', 'success')
    
    return redirect(url_for('admin_bookings'))

@app.route('/admin/users')
@login_required
@admin_required
def admin_users():
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@app.route('/admin/payments')
@login_required
@admin_required
def admin_payments():
    payments = Payment.query.order_by(Payment.created_at.desc()).all()
    return render_template('admin/payments.html', payments=payments)

# ========== AUTHENTICATION ROUTES ==========

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user, remember=True)
            flash('Login successful!', 'success')
            
            # Redirect admin to admin panel
            if user.is_admin:
                return redirect(url_for('admin_dashboard'))
            
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        phone = request.form.get('phone')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validation
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return redirect(url_for('register'))
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return redirect(url_for('register'))
        
        # Create new user
        hashed_password = generate_password_hash(password)
        new_user = User(
            username=username,
            email=email,
            phone=phone,
            password=hashed_password,
            is_admin=False
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

@app.route('/profile')
@login_required
def profile():
    user_bookings = Booking.query.filter_by(user_id=current_user.id).order_by(Booking.booking_date.desc()).all()
    user_payments = Payment.query.filter_by(user_id=current_user.id).order_by(Payment.created_at.desc()).all()
    
    return render_template('profile.html', 
                         user=current_user,
                         bookings=user_bookings,
                         payments=user_payments)

# ========== API ROUTES ==========

@app.route('/api/properties')
def api_properties():
    properties = Property.query.filter_by(is_available=True, is_booked=False).all()
    properties_data = []
    
    for prop in properties:
        properties_data.append({
            'id': prop.id,
            'title': prop.title,
            'price': prop.price,
            'location': prop.location,
            'latitude': prop.latitude,
            'longitude': prop.longitude,
            'type': prop.property_type,
            'bedrooms': prop.bedrooms,
            'image': json.loads(prop.images)[0] if prop.images else '/static/images/house-placeholder.jpg'
        })
    
    return jsonify(properties_data)

@app.route('/api/search/properties')
def api_search_properties():
    location = request.args.get('location', '')
    property_type = request.args.get('type', '')
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    
    query = Property.query.filter_by(is_available=True, is_booked=False)
    
    if location:
        query = query.filter(Property.location.ilike(f'%{location}%'))
    
    if property_type and property_type != 'all':
        query = query.filter_by(property_type=property_type)
    
    if min_price:
        query = query.filter(Property.price >= min_price)
    
    if max_price:
        query = query.filter(Property.price <= max_price)
    
    properties = query.all()
    
    result = []
    for prop in properties:
        result.append({
            'id': prop.id,
            'title': prop.title,
            'price': prop.price,
            'location': prop.location,
            'type': prop.property_type,
            'bedrooms': prop.bedrooms,
            'size': prop.size,
            'deposit': prop.deposit
        })
    
    return jsonify(result)

# ========== ERROR HANDLERS ==========

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

# ========== MAIN ==========

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)