import pymysql
pymysql.install_as_MySQLdb()

from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta

# Initialize Flask application
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Set your secret key for session management
app.permanent_session_lifetime = timedelta(minutes=30)  # Optional session timeout

<<<<<<< HEAD
# Configure MySQL connection settings (root connection for initial setup)
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'waterbilling'

# Configure MySQL settings
# app.config['MYSQL_HOST'] = 'localhost'
# app.config['MYSQL_USER'] = 'sharls'
# app.config['MYSQL_PASSWORD'] = 'sharls'
# app.config['MYSQL_DB'] = 'waterbilling'

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

        # Create the 'users' table if it does not exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL
            )
        """)
        print("Table 'users' ensured in the database.")
        
        cursor.close()
        connection.close()
    except pymysql.MySQLError as e:
        print(f"Error creating tables: {e}")

# Run the database and table creation checks
create_database_if_not_exists()
create_tables_if_not_exists()

# Initialize MySQL (after the database and table creation checks)
mysql = MySQL(app)

# Route for authentication page (index)
@app.route('/', methods=['GET', 'POST'])
=======
# Configure MySQL settings
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'sharls'
app.config['MYSQL_PASSWORD'] = 'sharls'
app.config['MYSQL_DB'] = 'waterbilling'

# Initialize MySQL
mysql = MySQL(app)

# Route for authentication page (index)
@app.route('/')
>>>>>>> f90c0c935888b5046800315285ef3b36ca873b9e
def index():
    return render_template('index.html')

# Route for login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        
<<<<<<< HEAD
        if user and check_password_hash(user[3], password):  # Password is in the 4th position
            session['user_id'] = user[0]  # Store user ID in session
            flash('Login successful!')
            return redirect(url_for('home'))
        else:
            flash('Invalid credentials. Please try again.')
    return render_template('index.html')
=======
        if user and check_password_hash(user[2], password):
            session['user_id'] = user[0]  # Store user ID in session
            flash('Login successful!')  # Show success message
            return redirect(url_for('home'))  # Redirect to home after successful login
        else:
            flash('Invalid credentials. Please try again.')  # Show error message
    return render_template('index.html')  # Render index page again for login
>>>>>>> f90c0c935888b5046800315285ef3b36ca873b9e

# Route for register page
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            flash('Email is already registered. Please use a different email.')
<<<<<<< HEAD
            return redirect(url_for('index'))
        
        cursor.execute("INSERT INTO users (name, email, password) VALUES (%s, %s, %s)", 
                       (name, email, hashed_password))
        mysql.connection.commit()
        flash('Registration successful! You can now log in.')
        return redirect(url_for('index'))
    
    return render_template('index.html')
=======
            return redirect(url_for('index'))  # Redirect to index to show the form again
        
        cursor.execute("INSERT INTO users (name, email, password) VALUES (%s, %s, %s)", (name, email, hashed_password))
        mysql.connection.commit()  # Commit changes to the database
        flash('Registration successful! You can now log in.')  # Show success message
        return redirect(url_for('index'))  # Redirect to index after successful registration
    
    return render_template('index.html')  # Render index page for registration
>>>>>>> f90c0c935888b5046800315285ef3b36ca873b9e

# Route for the dashboard page
@app.route('/home')
def home():
<<<<<<< HEAD
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('home.html')

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
=======
    if 'user_id' not in session:  # Check if user is logged in
        return redirect(url_for('login'))  # Redirect to login if not logged in
    return render_template('home.html')  # Render home page if logged in

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
>>>>>>> f90c0c935888b5046800315285ef3b36ca873b9e
