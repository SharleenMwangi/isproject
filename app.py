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

# Configure MySQL settings
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'sharls'
app.config['MYSQL_PASSWORD'] = 'sharls'
app.config['MYSQL_DB'] = 'waterbilling'

# Initialize MySQL
mysql = MySQL(app)

# Route for authentication page (index)
@app.route('/')
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
        
        if user and check_password_hash(user[2], password):
            session['user_id'] = user[0]  # Store user ID in session
            flash('Login successful!')  # Show success message
            return redirect(url_for('home'))  # Redirect to home after successful login
        else:
            flash('Invalid credentials. Please try again.')  # Show error message
    return render_template('index.html')  # Render index page again for login

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
            return redirect(url_for('index'))  # Redirect to index to show the form again
        
        cursor.execute("INSERT INTO users (name, email, password) VALUES (%s, %s, %s)", (name, email, hashed_password))
        mysql.connection.commit()  # Commit changes to the database
        flash('Registration successful! You can now log in.')  # Show success message
        return redirect(url_for('index'))  # Redirect to index after successful registration
    
    return render_template('index.html')  # Render index page for registration

# Route for the dashboard page
@app.route('/home')
def home():
    if 'user_id' not in session:  # Check if user is logged in
        return redirect(url_for('login'))  # Redirect to login if not logged in
    return render_template('home.html')  # Render home page if logged in

# Run the app
if __name__ == '__main__':
    app.run(debug=True)