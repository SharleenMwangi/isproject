import pymysql
pymysql.install_as_MySQLdb()

from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_socketio import SocketIO, emit
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta

# Initialize Flask application
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Set your secret key for session management
app.permanent_session_lifetime = timedelta(minutes=30)  # Optional session timeout

# Configure MySQL connection settings
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'waterbilling'

# Initialize MySQL and Flask-SocketIO
mysql = MySQL(app)
socketio = SocketIO(app)

# Function to check if the database exists, and create it if it doesn’t
def create_database_if_not_exists():
    try:
        connection = pymysql.connect(
            host=app.config['MYSQL_HOST'],
            user=app.config['MYSQL_USER'],
            password=app.config['MYSQL_PASSWORD']
        )
        cursor = connection.cursor()
        
        # Check if the database already exists
        cursor.execute("SHOW DATABASES LIKE 'waterbilling'")
        result = cursor.fetchone()
        
        # Create the database if it does not exist
        if not result:
            cursor.execute("CREATE DATABASE waterbilling")
            print("Database 'waterbilling' created.")
        else:
            print("Database 'waterbilling' already exists.")
        
        cursor.close()
        connection.close()
    except pymysql.MySQLError as e:
        print(f"Error creating database: {e}")

# Function to create necessary tables if they do not exist
def create_tables_if_not_exists():
    try:
        connection = pymysql.connect(
            host=app.config['MYSQL_HOST'],
            user=app.config['MYSQL_USER'],
            password=app.config['MYSQL_PASSWORD'],
            database=app.config['MYSQL_DB']
        )
        cursor = connection.cursor()

        # Create the 'users' table if it does not exist, with a meter_number field
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                meter_number VARCHAR(50) NOT NULL,  -- New column for meter number
                is_admin BOOLEAN DEFAULT FALSE  -- Field for admin status
            )
        """)

        # Create the 'messages' table for storing messages
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INT AUTO_INCREMENT PRIMARY KEY,
                sender_id INT NOT NULL,
                receiver_id INT NOT NULL,
                message TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (sender_id) REFERENCES users(id),
                FOREIGN KEY (receiver_id) REFERENCES users(id)
            )
        """)

        print("Tables ensured in the database.")
        cursor.close()
        connection.close()
    except pymysql.MySQLError as e:
        print(f"Error creating tables: {e}")

# Run the database and table creation checks
create_database_if_not_exists()
create_tables_if_not_exists()

# Session timeout extension on user activity
@app.before_request
def session_timeout_check():
    if 'user_id' in session:
        session.modified = True

# Function to get the current logged-in user
def get_user_from_session():
    user_id = session.get('user_id')
    if not user_id:
        return None
    
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    
    return user

# Function to send and save messages in the database
def save_message(sender_id, receiver_id, message):
    cursor = mysql.connection.cursor()
    cursor.execute("""
        INSERT INTO messages (sender_id, receiver_id, message)
        VALUES (%s, %s, %s)
    """, (sender_id, receiver_id, message))
    mysql.connection.commit()
    cursor.close()

# WebSocket route for receiving and broadcasting messages
@socketio.on('send_message')
def handle_message(data):
    sender_id = data['sender_id']
    receiver_id = data['receiver_id']
    message = data['message']
    
    # Save message in the database
    save_message(sender_id, receiver_id, message)
    
    # Broadcast message to admin and users
    emit('receive_message', data, broadcast=True)
@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE email = %s AND is_admin = TRUE", (email,))
        admin = cursor.fetchone()
        cursor.close()

        if admin:
            print(f"Stored Hash: {admin[3]}")  # Debugging stored hash
            print(f"Entered Password: {password}")
            if check_password_hash(admin[3], password):  # Validate password
                session['admin_id'] = admin[0]  # Store admin ID in session
                session['is_admin'] = True  # Mark session as admin
                print("Admin login successful. Redirecting to dashboard.")
                flash('Admin login successful!', 'success')
                return redirect(url_for('admin_dashboard'))  # Redirect to admin dashboard
            else:
                print("Invalid password.")
                flash('Invalid password.', 'error')
        else:
            print("Admin user not found.")
            flash('Admin user not found.', 'error')

    return render_template('admin_login.html')

from MySQLdb.cursors import DictCursor

@app.route('/admin/dashboard', methods=['GET', 'POST'])
def admin_dashboard():
    if not session.get('is_admin'):
        flash("Access denied. Admins only.")
        return redirect(url_for('admin_login'))

    # Use DictCursor to get dictionary-like results
    cursor = mysql.connection.cursor(DictCursor)

    # Fetch user data for the table
    cursor.execute("""
        SELECT id, name, email, meter_number, created_at, is_admin, 
               CASE WHEN is_admin = TRUE THEN 'active' ELSE 'inactive' END AS status
        FROM users
    """)
    users = cursor.fetchall()

    # Fetch data for user registration graph
    cursor.execute("""
        SELECT DATE(created_at) AS registration_date, COUNT(*) AS user_count
        FROM users
        WHERE is_admin = FALSE
        GROUP BY DATE(created_at)
        ORDER BY registration_date
    """)
    registration_data = cursor.fetchall()

    cursor.close()

    dates = [row['registration_date'] for row in registration_data]
    counts = [row['user_count'] for row in registration_data]

    return render_template(
        'admin_dashboard.html',
        users=users,
        dates=dates,
        counts=counts
    )
@app.route('/admin/edit_user/<int:user_id>', methods=['GET', 'POST'])
def edit_user(user_id):
    if not session.get('is_admin'):
        flash("Access denied. Admins only.")
        return redirect(url_for('admin_login'))

    # Retrieve user from the database
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()

    if not user:
        flash("User not found.")
        return redirect(url_for('admin_dashboard'))

    if request.method == 'POST':
        # Handle user update logic here
        name = request.form['name']
        email = request.form['email']
        meter_number = request.form['meter_number']

        cursor = mysql.connection.cursor()
        cursor.execute("""
            UPDATE users SET name = %s, email = %s, meter_number = %s WHERE id = %s
        """, (name, email, meter_number, user_id))
        mysql.connection.commit()
        cursor.close()

        flash('User updated successfully!')
        return redirect(url_for('admin_dashboard'))

    return render_template('edit_user.html', user=user)
@app.route('/delete_user/<int:user_id>', methods=['GET', 'POST'])
def delete_user(user_id):
    # Your code to handle user deletion
    # For example:
    user = User.query.get(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
        flash('User deleted successfully!', 'success')
    else:
        flash('User not found!', 'error')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/reports', methods=['GET', 'POST'])
def admin_reports():
    if not session.get('is_admin'):
        flash("Access denied. Admins only.")
        return redirect(url_for('admin_login'))

    users = []
    if request.method == 'POST':
        search_query = request.form.get('search')
        cursor = mysql.connection.cursor(DictCursor)
        cursor.execute("""
            SELECT id, name, email, meter_number
            FROM users
            WHERE name LIKE %s OR email LIKE %s OR meter_number LIKE %s
        """, (f'%{search_query}%', f'%{search_query}%', f'%{search_query}%'))
        users = cursor.fetchall()
        cursor.close()

    return render_template('admin_dashboard.html', users=users)


@app.route('/admin/edit_usage/<int:user_id>', methods=['GET', 'POST'])
def edit_usage(user_id):
    if not session.get('is_admin'):
        flash("Access denied. Admins only.")
        return redirect(url_for('admin_login'))

    # Retrieve data for a specific user and month/year
    year = request.args.get('year', default=2024)
    month = request.args.get('month', default=1)

    cursor = mysql.connection.cursor(DictCursor)
    cursor.execute("""
        SELECT usage_units, billing_amount, payment_status
        FROM usage
        WHERE user_id = %s AND year = %s AND month = %s
    """, (user_id, year, month))
    data = cursor.fetchone()
    cursor.close()

    if not data:
        flash("No data found for the specified month/year.")
        return redirect(url_for('admin_reports'))

    return render_template(
        'edit_usage.html',
        user_id=user_id,
        year=year,
        month=month,
        usage_units=data['usage_units'],
        billing_amount=data['billing_amount'],
        payment_status=data['payment_status']
    )


@app.route('/admin/update_usage/<int:user_id>', methods=['POST'])
def update_usage(user_id):
    if not session.get('is_admin'):
        flash("Access denied. Admins only.")
        return redirect(url_for('admin_login'))

    # Update usage data
    year = request.form['year']
    month = request.form['month']
    usage_units = request.form['usage_units']
    billing_amount = request.form['billing_amount']
    payment_status = request.form['payment_status']

    cursor = mysql.connection.cursor()
    cursor.execute("""
        UPDATE usage
        SET usage_units = %s, billing_amount = %s, payment_status = %s
        WHERE user_id = %s AND year = %s AND month = %s
    """, (usage_units, billing_amount, payment_status, user_id, year, month))
    mysql.connection.commit()
    cursor.close()

    flash("User data updated successfully!")
    return redirect(url_for('admin_reports'))




    # Handle POST logic if needed (e.g., forms submitted on the dashboard)
    if request.method == 'POST':
        # Add logic for POST requests here
        pass


# Route for authentication page (index)
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        form_type = request.form.get('form_type')  # Safe access
        email = request.form.get('email')  # Safe access
        password = request.form.get('password')  # Safe access
        
        if not email or not password:
            flash('Email and password are required.')
            return render_template('index.html')

        cursor = mysql.connection.cursor()

        if form_type == 'login':
            # Handle login
            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()
            if user and check_password_hash(user[3], password):  # Password is in the 4th position
                session['user_id'] = user[0]  # Store user ID in session
                flash('Login successful!')
                return redirect(url_for('home'))
            else:
                flash('Invalid credentials. Please try again.')

        elif form_type == 'register':
            # Handle registration
            name = request.form.get('name')  # Make sure 'name' is submitted
            meter_number = request.form.get('meter_number')  # Get the meter number from the form
            
            if not name or not meter_number:
                flash('Name and Meter Number are required for registration.')
                return render_template('index.html')

            # Check if the user already exists
            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            existing_user = cursor.fetchone()
            if existing_user:
                flash('Email is already registered. Please use a different email.')
            else:
                hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
                cursor.execute("INSERT INTO users (name, email, password, meter_number) VALUES (%s, %s, %s, %s)", 
                               (name, email, hashed_password, meter_number))
                mysql.connection.commit()
                flash('Registration successful! You can now log in.')

    return render_template('index.html')



@app.route('/home')
def home():
    user = get_user_from_session()
    if not user:
        flash('Please log in to access the home page.')
        return redirect(url_for('index'))

    # Fetch usage
    cursor = mysql.connection.cursor(DictCursor)
    cursor.execute(
        'SELECT year, month, usage_units FROM `usage` WHERE user_id = %s ORDER BY year, month', (user['id'],)
    )
    usage_data = cursor.fetchall()

    # Fetch charges
    cursor = mysql.connection.cursor(DictCursor)
    cursor.execute(
        'SELECT year, month, total_charges FROM `charges` WHERE user_id = %s ORDER BY year, month', (user['id'],)
    )
    charges_data = cursor.fetchall()

    # Fetch payments
    cursor = mysql.connection.cursor(DictCursor)
    cursor.execute(
        'SELECT payment_date, amount, status FROM `payments` WHERE user_id = %s ORDER BY payment_date DESC', (user['id'],)
    )
    payments_data = cursor.fetchall()

    cursor.close()

    return render_template('home.html', usage_data=usage_data, charges_data=charges_data, payments_data=payments_data)


def get_user_from_session():
    user_id = session.get('user_id')
    if not user_id:
        return None
    
    cursor = mysql.connection.cursor(DictCursor)  # Use DictCursor here
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    
    return user


    # Route for the settings page
@app.route('/settings')
def settings():
    print("Settings route accessed")
    user = get_user_from_session()
    if not user:
        flash('Please log in to access settings.')
        return redirect(url_for('index'))
    return render_template('settings.html', user=user)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))



# Run the app with SocketIO
if __name__ == '__main__':
    socketio.run(app, debug=True)
from flask import render_template, request, redirect, url_for, session
from your_database_module import db, User, Message, Report, AdminSettings
