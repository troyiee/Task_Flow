import sqlite3
import json
import os
import random
import time
from datetime import timedelta
from functools import wraps
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import uuid
from PIL import Image
import mimetypes
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from dotenv import load_dotenv


load_dotenv()
# Import notification system after creating the app
# from notification_system import TaskNotificationSystem, add_notification_routes

app = Flask(__name__)
app.secret_key = '12333'  # Change this to a secure secret key
app.permanent_session_lifetime = timedelta(days=7)

# Configuration
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp', 'mp4', 'avi', 'mov', 'wmv', 'flv', 'webm'}
MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB max file size

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Create upload directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

pending_users: dict[str, dict[str, str]] = {}

DB_FILE = 'app.db'
SESSION_FILE = 'session.json'

# Brevo API Key - IMPORTANT: Move this to environment variables in production
BREVO_API_KEY = os.getenv('BREVO_API_KEY')

# Initialize notification system
notification_system = None

# --- Database Setup ---
def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def is_video_file(filename):
    video_extensions = {'mp4', 'avi', 'mov', 'wmv', 'flv', 'webm'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in video_extensions

def create_thumbnail(filepath, thumbnail_path, size=(300, 300)):
    """Create thumbnail for images"""
    try:
        with Image.open(filepath) as img:
            img.thumbnail(size, Image.Resampling.LANCZOS)
            img.save(thumbnail_path, optimize=True, quality=85)
        return True
    except Exception as e:
        print(f"Error creating thumbnail: {e}")
        return False

def init_db():
    conn = get_db()
    c = conn.cursor()

    # Users table with email field
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL
    )''')

    # Tasks table
    c.execute('''CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        due_date DATE,
        priority TEXT DEFAULT 'medium',
        completed INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )''')
    
    # Media table for file uploads
    c.execute('''CREATE TABLE IF NOT EXISTS media (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        task_id INTEGER,
        filename TEXT NOT NULL,
        original_filename TEXT NOT NULL,
        file_type TEXT NOT NULL,
        file_size INTEGER NOT NULL,
        upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        description TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id),
        FOREIGN KEY(task_id) REFERENCES tasks(id)
    )''')
    
    # Password reset tokens table
    c.execute('''CREATE TABLE IF NOT EXISTS password_reset_tokens (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        token TEXT UNIQUE NOT NULL,
        expires_at TIMESTAMP NOT NULL,
        used INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )''')
    
    conn.commit()
    conn.close()

def send_otp_email(to_email, otp):
    try:
        configuration = sib_api_v3_sdk.Configuration()
        configuration.api_key['api-key'] = BREVO_API_KEY
        api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))

        subject = "Your OTP Verification Code"
        sender = {"name": "Task Scheduler", "email": "garciaraffitroy08@gmail.com"}
        html_content = f"""
        <html>
        <body>
            <h2>Task Scheduler - Email Verification</h2>
            <p>Hello,</p>
            <p>Your OTP verification code is:</p>
            <h1 style="color: #007bff; font-size: 32px; letter-spacing: 5px;">{otp}</h1>
            <p>Please enter this code to complete your registration.</p>
            <p>This code will expire in 10 minutes.</p>
            <br>
            <p>Best regards,<br>Task Scheduler Team</p>
        </body>
        </html>
        """
        to = [{"email": to_email}]

        send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
            to=to,
            html_content=html_content,
            sender=sender,
            subject=subject
        )

        api_response = api_instance.send_transac_email(send_smtp_email)
        print(f"Email sent successfully to {to_email}. Message ID: {api_response}")
        return True
    except ApiException as e:
        print(f"Brevo API Error: {e}")
        print(f"Error details: {e.body if hasattr(e, 'body') else 'No additional details'}")
        return False
    except Exception as e:
        print(f"General error sending OTP: {e}")
        return False

def send_password_reset_email(to_email, username, reset_url):
    try:
        configuration = sib_api_v3_sdk.Configuration()
        configuration.api_key['api-key'] = BREVO_API_KEY
        api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))

        subject = "Password Reset Request - Task Scheduler"
        sender = {"name": "Task Scheduler", "email": "garciaraffitroy08@gmail.com"}
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #007bff; text-align: center;">Task Scheduler - Password Reset</h2>
                <p>Hello {username},</p>
                <p>We received a request to reset your password for your Task Scheduler account.</p>
                <p>Click the button below to reset your password:</p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{reset_url}" style="background-color: #007bff; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">Reset Password</a>
                </div>
                <p>If the button doesn't work, you can copy and paste this link into your browser:</p>
                <p style="word-break: break-all; color: #007bff;">{reset_url}</p>
                <p><strong>This link will expire in 1 hour for security reasons.</strong></p>
                <p>If you didn't request this password reset, please ignore this email. Your password will remain unchanged.</p>
                <br>
                <p>Best regards,<br>Task Scheduler Team</p>
            </div>
        </body>
        </html>
        """
        to = [{"email": to_email}]

        send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
            to=to,
            html_content=html_content,
            sender=sender,
            subject=subject
        )

        api_response = api_instance.send_transac_email(send_smtp_email)
        print(f"Password reset email sent successfully to {to_email}. Message ID: {api_response}")
        return True
    except ApiException as e:
        print(f"Brevo API Error: {e}")
        print(f"Error details: {e.body if hasattr(e, 'body') else 'No additional details'}")
        return False
    except Exception as e:
        print(f"General error sending password reset email: {e}")
        return False

# --- Persistent Session (JSON) ---
def load_session():
    if not os.path.exists(SESSION_FILE):
        return {}
    try:
        with open(SESSION_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_session(sess):
    try:
        with open(SESSION_FILE, 'w') as f:
            json.dump(sess, f)
    except Exception as e:
        print(f"Error saving session: {e}")

# --- Auth Decorator ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def calculate_task_progress(task, media_timeline):
    """Calculate task progress based on media uploads and completion status"""
    if task['completed']:
        return 100
    
    # Basic progress calculation based on media count and due date
    media_count = len(media_timeline)
    
    if not task['due_date']:
        # If no due date, base progress on media count
        return min(media_count * 20, 80)  # Max 80% without completion
    
    # Calculate progress based on time elapsed and media uploads
    try:
        due_date = datetime.strptime(task['due_date'], '%Y-%m-%d')
        today = datetime.now()
        
        if today >= due_date:
            return 90  # Nearly complete if overdue but not marked complete
        
        # Time-based progress calculation
        time_progress = min((today - datetime.strptime(task['due_date'], '%Y-%m-%d')).days * 10, 60)
        media_progress = min(media_count * 15, 30)
        
        return min(time_progress + media_progress, 80)
    except ValueError:
        # If date parsing fails, fallback to media-based progress
        return min(media_count * 20, 80)

def check_task_notifications(user_id, task_data):
    """Check if a task needs immediate notification"""
    if not notification_system or not task_data.get('due_date'):
        return
    
    try:
        from datetime import datetime, date, timedelta
        
        due_date = datetime.strptime(task_data['due_date'], '%Y-%m-%d').date()
        today = date.today()
        tomorrow = today + timedelta(days=1)
        
        # Get user info
        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT username, email FROM users WHERE id = ?', (user_id,))
        user = c.fetchone()
        conn.close()
        
        if not user:
            return
        
        # Check if task needs immediate notification
        notification_type = None
        if due_date < today:
            notification_type = 'overdue'
        elif due_date == today:
            notification_type = 'due_today'
        elif due_date == tomorrow:
            notification_type = 'due_tomorrow'
        
        if notification_type:
            # Send immediate notification for this task
            notification_system.send_immediate_task_notification(
                user_id, user['username'], user['email'], task_data, notification_type
            )
            
    except Exception as e:
        print(f"Error checking task notifications: {e}")

def generate_task_report(tasks, username):
    """Generate a formatted text report for selected tasks"""
    report_lines = []
    
    # Header
    report_lines.append("=" * 80)
    report_lines.append(f"TASK SCHEDULER - TASK REPORT")
    report_lines.append("=" * 80)
    report_lines.append(f"Generated for: {username}")
    report_lines.append(f"Generated on: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}")
    report_lines.append(f"Total Tasks: {len(tasks)}")
    report_lines.append("")
    
    # Summary
    completed_count = sum(1 for task in tasks if task['completed'])
    pending_count = len(tasks) - completed_count
    high_priority = sum(1 for task in tasks if task['priority'] == 'high' and not task['completed'])
    medium_priority = sum(1 for task in tasks if task['priority'] == 'medium' and not task['completed'])
    low_priority = sum(1 for task in tasks if task['priority'] == 'low' and not task['completed'])
    
    report_lines.append("SUMMARY:")
    report_lines.append("-" * 40)
    report_lines.append(f"Completed Tasks: {completed_count}")
    report_lines.append(f"Pending Tasks: {pending_count}")
    report_lines.append(f"High Priority: {high_priority}")
    report_lines.append(f"Medium Priority: {medium_priority}")
    report_lines.append(f"Low Priority: {low_priority}")
    report_lines.append("")
    
    # Group tasks by priority and status
    high_priority_tasks = [t for t in tasks if t['priority'] == 'high' and not t['completed']]
    medium_priority_tasks = [t for t in tasks if t['priority'] == 'medium' and not t['completed']]
    low_priority_tasks = [t for t in tasks if t['priority'] == 'low' and not t['completed']]
    completed_tasks = [t for t in tasks if t['completed']]
    
    # High Priority Tasks
    if high_priority_tasks:
        report_lines.append("HIGH PRIORITY TASKS:")
        report_lines.append("-" * 40)
        for task in high_priority_tasks:
            report_lines.append(f"• {task['title']}")
            if task['due_date']:
                report_lines.append(f"  Due: {task['due_date']}")
            if task['media_count'] > 0:
                report_lines.append(f"  Media Files: {task['media_count']}")
            report_lines.append("")
    
    # Medium Priority Tasks
    if medium_priority_tasks:
        report_lines.append("MEDIUM PRIORITY TASKS:")
        report_lines.append("-" * 40)
        for task in medium_priority_tasks:
            report_lines.append(f"• {task['title']}")
            if task['due_date']:
                report_lines.append(f"  Due: {task['due_date']}")
            if task['media_count'] > 0:
                report_lines.append(f"  Media Files: {task['media_count']}")
            report_lines.append("")
    
    # Low Priority Tasks
    if low_priority_tasks:
        report_lines.append("LOW PRIORITY TASKS:")
        report_lines.append("-" * 40)
        for task in low_priority_tasks:
            report_lines.append(f"• {task['title']}")
            if task['due_date']:
                report_lines.append(f"  Due: {task['due_date']}")
            if task['media_count'] > 0:
                report_lines.append(f"  Media Files: {task['media_count']}")
            report_lines.append("")
    
    # Completed Tasks
    if completed_tasks:
        report_lines.append("COMPLETED TASKS:")
        report_lines.append("-" * 40)
        for task in completed_tasks:
            report_lines.append(f"✓ {task['title']}")
            if task['due_date']:
                report_lines.append(f"  Due: {task['due_date']}")
            if task['media_count'] > 0:
                report_lines.append(f"  Media Files: {task['media_count']}")
            report_lines.append("")
    
    # Footer
    report_lines.append("=" * 80)
    report_lines.append("End of Report")
    report_lines.append("=" * 80)
    
    return "\n".join(report_lines)

# --- Routes ---
@app.route('/')
def home():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Handle resend OTP request
        if request.form.get('resend') == 'true':
            if 'pending_user' in session:
                username = session['pending_user']
                user_data = pending_users.get(username)
                if user_data:
                    # Generate new OTP
                    new_otp = str(random.randint(100000, 999999))
                    pending_users[username]['otp'] = new_otp
                    
                    print(f"Resending OTP for {username}: {new_otp}")  # Debug log
                    
                    success = send_otp_email(user_data['email'], new_otp)
                    if success:
                        return '<div data-otp-sent></div>'
                    else:
                        return '<div data-otp-failed></div>'
            return '<div data-session-expired></div>'
        
        # Handle normal registration
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        email = request.form.get('email', '').strip()

        # Validation
        if not username or not password or not email:
            return '<div data-validation-error>All fields are required</div>'

        if len(password) < 6:
            return '<div data-validation-error>Password must be at least 6 characters</div>'

        conn = get_db()
        c = conn.cursor()
        
        # Check if username already exists
        c.execute('SELECT id FROM users WHERE username = ?', (username,))
        if c.fetchone():
            conn.close()
            return '<div data-register-exists></div>'
        
        # Check if email already exists
        c.execute('SELECT id FROM users WHERE email = ?', (email,))
        if c.fetchone():
            conn.close()
            return '<div data-email-exists>Email already registered</div>'
        
        conn.close()

        # Generate OTP and store user data
        otp = str(random.randint(100000, 999999))
        pending_users[username] = {
            'password': generate_password_hash(password), 
            'email': email, 
            'otp': otp
        }
        
        print(f"Generated OTP for {username}: {otp}")  # Debug log
        print(f"Sending OTP to email: {email}")  # Debug log
        
        success = send_otp_email(email, otp)

        if success:
            session['pending_user'] = username
            return '<div data-otp-sent></div>'
        else:
            # Clean up pending user if email failed
            if username in pending_users:
                del pending_users[username]
            return '<div data-otp-failed></div>'

    return render_template('login.html')

@app.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    if 'pending_user' not in session:
        return redirect(url_for('register'))

    username = session['pending_user']

    if request.method == 'POST':
        user_input = request.form.get('otp', '').strip()
        user_data = pending_users.get(username)

        if not user_data:
            return '<div data-invalid-otp>Registration session expired. Please register again.</div>'

        if user_input == user_data['otp']:
            try:
                conn = get_db()
                c = conn.cursor()
                c.execute('INSERT INTO users (username, password, email) VALUES (?, ?, ?)', 
                         (username, user_data['password'], user_data['email']))
                conn.commit()
                conn.close()
                
                # Clean up
                del pending_users[username]
                session.pop('pending_user', None)
                
                return '<div data-register-success></div>'
            except Exception as e:
                print(f"Database error during registration: {e}")
                return '<div data-database-error>Registration failed. Please try again.</div>'
        else:
            return '<div data-invalid-otp></div>'

    return render_template('verify_otp.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        if not username or not password:
            return '<div data-validation-error>Username and password are required</div>'
        
        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT password FROM users WHERE username = ?', (username,))
        row = c.fetchone()
        conn.close()
        
        if row and check_password_hash(row['password'], password):
            session['username'] = username
            session.permanent = True
            # Save persistent session
            save_session({'username': username})
            return '<div data-login-success></div>'
        return '<div data-login-error>Invalid username or password</div>'
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    save_session({})
    return redirect(url_for('login'))

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        
        if not email:
            return '<div data-validation-error>Email address is required</div>'
        
        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT id, username FROM users WHERE email = ?', (email,))
        user = c.fetchone()
        conn.close()
        
        if user:
            # Generate reset token
            token = str(uuid.uuid4())
            expires_at = datetime.now() + timedelta(hours=1)
            
            conn = get_db()
            c = conn.cursor()
            c.execute('INSERT INTO password_reset_tokens (user_id, token, expires_at) VALUES (?, ?, ?)',
                     (user['id'], token, expires_at))
            conn.commit()
            conn.close()
            
            # Generate reset URL
            reset_url = url_for('reset_password', token=token, _external=True)
            
            # Send email
            success = send_password_reset_email(email, user['username'], reset_url)
            
            if success:
                return '<div data-reset-email-sent>Password reset email sent successfully. Please check your email.</div>'
            else:
                return '<div data-email-error>Failed to send reset email. Please try again later.</div>'
        else:
            # Don't reveal if email exists or not for security
            return '<div data-reset-email-sent>If an account with that email exists, a password reset link has been sent.</div>'
    
    return render_template('forgot_password.html')

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if request.method == 'POST':
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        
        if not password or not confirm_password:
            return '<div data-validation-error>Both password fields are required</div>'
        
        if password != confirm_password:
            return '<div data-validation-error>Passwords do not match</div>'
        
        if len(password) < 6:
            return '<div data-validation-error>Password must be at least 6 characters long</div>'
        
        # Verify token
        conn = get_db()
        c = conn.cursor()
        c.execute('''SELECT prt.user_id, prt.used, prt.expires_at, u.username 
                     FROM password_reset_tokens prt 
                     JOIN users u ON prt.user_id = u.id 
                     WHERE prt.token = ?''', (token,))
        token_data = c.fetchone()
        
        if not token_data:
            return '<div data-invalid-token>Invalid or expired reset link</div>'
        
        if token_data['used']:
            return '<div data-invalid-token>This reset link has already been used</div>'
        
        try:
            expires_at = datetime.fromisoformat(token_data['expires_at'])
        except ValueError:
            # Handle different datetime formats
            expires_at = datetime.strptime(token_data['expires_at'], '%Y-%m-%d %H:%M:%S.%f')
        
        if datetime.now() > expires_at:
            return '<div data-invalid-token>Reset link has expired</div>'
        
        # Update password
        hashed_password = generate_password_hash(password)
        c.execute('UPDATE users SET password = ? WHERE id = ?', (hashed_password, token_data['user_id']))
        
        # Mark token as used
        c.execute('UPDATE password_reset_tokens SET used = 1 WHERE token = ?', (token,))
        
        conn.commit()
        conn.close()
        
        return '<div data-reset-success>Password reset successfully. You can now login with your new password.</div>'
    
    # GET request - show reset form
    conn = get_db()
    c = conn.cursor()
    c.execute('''SELECT used, expires_at 
                 FROM password_reset_tokens 
                 WHERE token = ?''', (token,))
    token_data = c.fetchone()
    conn.close()
    
    if not token_data:
        return render_template('reset_password.html', valid_token=False, error="Invalid reset link")
    
    if token_data['used']:
        return render_template('reset_password.html', valid_token=False, error="This reset link has already been used")
    
    try:
        expires_at = datetime.fromisoformat(token_data['expires_at'])
    except ValueError:
        # Handle different datetime formats
        expires_at = datetime.strptime(token_data['expires_at'], '%Y-%m-%d %H:%M:%S.%f')
    
    if datetime.now() > expires_at:
        return render_template('reset_password.html', valid_token=False, error="Reset link has expired")
    
    return render_template('reset_password.html', valid_token=True, token=token)

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', username=session['username'])

@app.route('/gallery')
@login_required
def gallery():
    return render_template('gallery.html', username=session['username'])

# Enhanced Task API routes with notification integration
@app.route('/api/tasks', methods=['GET', 'POST'])
@login_required
def tasks_api():
    username = session['username']
    conn = get_db()
    c = conn.cursor()
    
    # Get user ID
    try:
        c.execute('SELECT id FROM users WHERE username = ?', (username,))
        user_row = c.fetchone()
        if not user_row:
            conn.close()
            return jsonify({'success': False, 'error': 'User not found'}), 404
        user_id = user_row['id']
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'error': f'Database error: {str(e)}'}), 500
    
    if request.method == 'GET':
        try:
            # Get all tasks for the user
            c.execute('SELECT * FROM tasks WHERE user_id = ? ORDER BY created_at DESC', (user_id,))
            tasks = []
            for row in c.fetchall():
                tasks.append({
                    'id': row['id'],
                    'title': row['title'],
                    'due_date': row['due_date'],
                    'priority': row['priority'],
                    'completed': bool(row['completed']),
                    'created_at': row['created_at'] if 'created_at' in row.keys() else ''
                })
            conn.close()
            return jsonify({'success': True, 'tasks': tasks})
        except Exception as e:
            conn.close()
            return jsonify({'success': False, 'error': f'Failed to fetch tasks: {str(e)}'}), 500
    
    elif request.method == 'POST':
        try:
            # Handle both JSON and form data
            if request.is_json:
                data = request.get_json()
            else:
                data = {
                    'title': request.form.get('title', '').strip(),
                    'due_date': request.form.get('due_date') or None,
                    'priority': request.form.get('priority', 'medium')
                }
            
            title = data.get('title', '').strip()
            due_date = data.get('due_date') or None
            priority = data.get('priority', 'medium')
            
            # Validation
            if not title:
                conn.close()
                return jsonify({'success': False, 'error': 'Task title is required'}), 400
            
            if due_date == '':
                due_date = None
            
            # Insert new task
            c.execute('''INSERT INTO tasks (user_id, title, due_date, priority, completed) 
                        VALUES (?, ?, ?, ?, 0)''', (user_id, title, due_date, priority))
            task_id = c.lastrowid
            conn.commit()
            
            # Get the created task
            c.execute('SELECT * FROM tasks WHERE id = ?', (task_id,))
            row = c.fetchone()
            
            if not row:
                conn.close()
                return jsonify({'success': False, 'error': 'Failed to retrieve created task'}), 500
            
            task = {
                'id': row['id'],
                'title': row['title'],
                'due_date': row['due_date'],
                'priority': row['priority'],
                'completed': bool(row['completed']),
                'created_at': row['created_at'] if 'created_at' in row.keys() else ''
            }
            
            # Check for immediate notifications
            check_task_notifications(user_id, task)
            
            conn.close()
            return jsonify({
                'success': True,
                'task': task,
                'message': 'Task added successfully'
            })
            
            
        except Exception as e:
            conn.close()
            print(f"Error adding task: {str(e)}")
            return jsonify({'success': False, 'error': f'Failed to add task: {str(e)}'}), 500

@app.route('/api/tasks/<int:task_id>', methods=['PUT', 'DELETE'])
@login_required
def task_detail_api(task_id):
    username = session['username']
    conn = get_db()
    c = conn.cursor()
    
    # Get user ID
    try:
        c.execute('SELECT id FROM users WHERE username = ?', (username,))
        user_row = c.fetchone()
        if not user_row:
            conn.close()
            return jsonify({'success': False, 'error': 'User not found'}), 404
        user_id = user_row['id']
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'error': f'Database error: {str(e)}'}), 500
    
    if request.method == 'PUT':
        try:
            # Handle both JSON and form data
            if request.is_json:
                data = request.get_json()
            else:
                data = request.form.to_dict()
            
            # Check if task exists and belongs to user
            c.execute('SELECT * FROM tasks WHERE id = ? AND user_id = ?', (task_id, user_id))
            old_task = c.fetchone()
            if not old_task:
                conn.close()
                return jsonify({'success': False, 'error': 'Task not found'}), 404
            
            # Build update query dynamically
            update_fields = []
            update_values = []
            
            if 'title' in data and data['title'].strip():
                update_fields.append('title = ?')
                update_values.append(data['title'].strip())
            if 'due_date' in data:
                update_fields.append('due_date = ?')
                update_values.append(data['due_date'] if data['due_date'] else None)
            if 'priority' in data:
                update_fields.append('priority = ?')
                update_values.append(data['priority'])
            if 'completed' in data:
                update_fields.append('completed = ?')
                completed_val = data['completed']
                if isinstance(completed_val, str):
                    completed_val = completed_val.lower() in ('true', '1', 'yes', 'on')
                update_values.append(1 if completed_val else 0)
                
                # Create completion notification
                if notification_system and completed_val and not old_task['completed']:
                    notification_system.create_in_app_notification(
                        user_id,
                        "🎉 Task Completed!",
                        f'Great job! You completed "{old_task["title"]}"',
                        'info',
                        task_id
                    )
            
            if not update_fields:
                conn.close()
                return jsonify({'success': False, 'error': 'No valid fields to update'}), 400
            
            # Perform update
            update_values.extend([task_id, user_id])
            query = f"UPDATE tasks SET {', '.join(update_fields)} WHERE id = ? AND user_id = ?"
            c.execute(query, update_values)
            conn.commit()
            
            # Get updated task
            c.execute('SELECT * FROM tasks WHERE id = ? AND user_id = ?', (task_id, user_id))
            row = c.fetchone()
            
            task = {
                'id': row['id'],
                'title': row['title'],
                'due_date': row['due_date'],
                'priority': row['priority'],
                'completed': bool(row['completed']),
                'created_at': row['created_at'] if 'created_at' in row.keys() else ''
            }
            
            # Check for immediate notifications if due date was updated
            if 'due_date' in data:
                check_task_notifications(user_id, task)
            
            conn.close()
            return jsonify({
                'success': True,
                'task': task,
                'message': 'Task updated successfully'
            })
            
        except Exception as e:
            conn.close()
            print(f"Error updating task: {str(e)}")
            return jsonify({'success': False, 'error': f'Failed to update task: {str(e)}'}), 500
    
    elif request.method == 'DELETE':
        try:
            # Check if task exists and belongs to user
            c.execute('SELECT title FROM tasks WHERE id = ? AND user_id = ?', (task_id, user_id))
            task_row = c.fetchone()
            if not task_row:
                conn.close()
                return jsonify({'success': False, 'error': 'Task not found'}), 404
            
            task_title = task_row['title']
            
            # Delete associated media files first
            c.execute('SELECT filename FROM media WHERE task_id = ? AND user_id = ?', (task_id, user_id))
            media_files = c.fetchall()
            
            # Delete media files from filesystem
            for media in media_files:
                try:
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], media['filename'])
                    if os.path.exists(filepath):
                        os.remove(filepath)
                    # Delete thumbnail
                    thumbnail_path = os.path.join(app.config['UPLOAD_FOLDER'], f"thumb_{media['filename']}")
                    if os.path.exists(thumbnail_path):
                        os.remove(thumbnail_path)
                except Exception as file_error:
                    print(f"Error deleting media file: {file_error}")
            
            # Delete media records
            c.execute('DELETE FROM media WHERE task_id = ? AND user_id = ?', (task_id, user_id))
            
            # Delete task
            c.execute('DELETE FROM tasks WHERE id = ? AND user_id = ?', (task_id, user_id))
            conn.commit()
            
            # Create deletion notification
            if notification_system:
                notification_system.create_in_app_notification(
                    user_id,
                    "🗑️ Task Deleted",
                    f'Task "{task_title}" has been permanently deleted',
                    'info'
                )
            
            conn.close()
            
            return jsonify({
                'success': True,
                'message': 'Task deleted successfully'
            })
            
        except Exception as e:
            conn.close()
            print(f"Error deleting task: {str(e)}")
            return jsonify({'success': False, 'error': f'Failed to delete task: {str(e)}'}), 500

@app.route('/api/stats')
@login_required
def stats_api():
    username = session['username']
    conn = get_db()
    c = conn.cursor()
    
    try:
        c.execute('SELECT id FROM users WHERE username = ?', (username,))
        user_row = c.fetchone()
        if not user_row:
            conn.close()
            return jsonify({'success': False, 'error': 'User not found'}), 404
        user_id = user_row['id']
        
        # Get task statistics
        c.execute('SELECT COUNT(*) as total FROM tasks WHERE user_id = ?', (user_id,))
        total_tasks = c.fetchone()['total']
        
        c.execute('SELECT COUNT(*) as completed FROM tasks WHERE user_id = ? AND completed = 1', (user_id,))
        completed_tasks = c.fetchone()['completed']
        
        c.execute('SELECT COUNT(*) as pending FROM tasks WHERE user_id = ? AND completed = 0', (user_id,))
        pending_tasks = c.fetchone()['pending']
        
        # Get overdue tasks
        c.execute('''SELECT COUNT(*) as overdue FROM tasks 
                    WHERE user_id = ? AND completed = 0 AND due_date IS NOT NULL AND due_date < date('now')''', (user_id,))
        overdue_tasks = c.fetchone()['overdue']
        
        # Get media statistics
        c.execute('SELECT COUNT(*) as total_media FROM media WHERE user_id = ?', (user_id,))
        total_media = c.fetchone()['total_media']
        
        c.execute('''SELECT COUNT(DISTINCT task_id) as tasks_with_media 
                    FROM media WHERE user_id = ? AND task_id IS NOT NULL''', (user_id,))
        tasks_with_media = c.fetchone()['tasks_with_media']
        
        # Calculate completion rate
        completion_rate = 0
        if total_tasks > 0:
            completion_rate = round((completed_tasks / total_tasks) * 100)
        
        conn.close()
        return jsonify({
            'success': True,
            'stats': {
                'total_tasks': total_tasks,
                'completed_tasks': completed_tasks,
                'pending_tasks': pending_tasks,
                'overdue_tasks': overdue_tasks,
                'total_media': total_media,
                'tasks_with_media': tasks_with_media,
                'completion_rate': completion_rate
            }
        })
        
    except Exception as e:
        conn.close()
        print(f"Error loading stats: {str(e)}")
        return jsonify({'success': False, 'error': f'Failed to load stats: {str(e)}'}), 500

# Media API routes
@app.route('/api/media', methods=['GET', 'POST', 'DELETE'])
@login_required
def media_api():
    username = session['username']
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT id FROM users WHERE username = ?', (username,))
    user_row = c.fetchone()
    if not user_row:
        conn.close()
        return jsonify({'success': False, 'error': 'User not found'})
    user_id = user_row['id']
    
    if request.method == 'GET':
        task_id = request.args.get('task_id')
        if task_id:
            c.execute('SELECT * FROM media WHERE user_id = ? AND task_id = ? ORDER BY upload_date DESC', (user_id, task_id))
        else:
            c.execute('SELECT * FROM media WHERE user_id = ? ORDER BY upload_date DESC', (user_id,))
        
        media_files = []
        for row in c.fetchall():
            media_files.append({
                'id': row['id'],
                'filename': row['filename'],
                'original_filename': row['original_filename'],
                'file_type': row['file_type'],
                'file_size': row['file_size'],
                'upload_date': row['upload_date'],
                'description': row['description'],
                'task_id': row['task_id'],
                'url': url_for('static', filename=f'uploads/{row["filename"]}'),
                'is_video': is_video_file(row['filename'])
            })
        conn.close()
        return jsonify({'success': True, 'media': media_files})
    
    elif request.method == 'POST':
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file selected'})
        
        file = request.files['file']
        description = request.form.get('description', '')
        task_id = request.form.get('task_id')
        
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'})
        
        if file and allowed_file(file.filename):
            # Generate unique filename
            file_extension = file.filename.rsplit('.', 1)[1].lower()
            unique_filename = f"{uuid.uuid4().hex}.{file_extension}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            
            try:
                file.save(filepath)
                file_size = os.path.getsize(filepath)
                
                # Create thumbnail for images
                if not is_video_file(unique_filename):
                    thumbnail_filename = f"thumb_{unique_filename}"
                    thumbnail_path = os.path.join(app.config['UPLOAD_FOLDER'], thumbnail_filename)
                    create_thumbnail(filepath, thumbnail_path)
                
                # Save to database
                c.execute('''INSERT INTO media (user_id, task_id, filename, original_filename, 
                           file_type, file_size, description) VALUES (?, ?, ?, ?, ?, ?, ?)''',
                         (user_id, task_id if task_id else None, unique_filename, 
                          file.filename, file_extension, file_size, description))
                conn.commit()
                media_id = c.lastrowid
                conn.close()
                
                return jsonify({
                    'success': True,
                    'media': {
                        'id': media_id,
                        'filename': unique_filename,
                        'original_filename': file.filename,
                        'file_type': file_extension,
                        'file_size': file_size,
                        'description': description,
                        'task_id': int(task_id) if task_id else None,
                        'url': url_for('static', filename=f'uploads/{unique_filename}'),
                        'is_video': is_video_file(unique_filename),
                        'upload_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                })
            except Exception as e:
                conn.close()
                return jsonify({'success': False, 'error': f'Failed to upload file: {str(e)}'})
        else:
            conn.close()
            return jsonify({'success': False, 'error': 'File type not allowed'})
    
    elif request.method == 'DELETE':
        data = request.get_json()
        media_id = data.get('id')
        
        # Get file info before deletion
        c.execute('SELECT filename FROM media WHERE id = ? AND user_id = ?', (media_id, user_id))
        row = c.fetchone()
        if row:
            filename = row['filename']
            # Delete from database
            c.execute('DELETE FROM media WHERE id = ? AND user_id = ?', (media_id, user_id))
            conn.commit()
            
            # Delete file from filesystem
            try:
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                if os.path.exists(filepath):
                    os.remove(filepath)
                
                # Delete thumbnail if exists
                thumbnail_filename = f"thumb_{filename}"
                thumbnail_path = os.path.join(app.config['UPLOAD_FOLDER'], thumbnail_filename)
                if os.path.exists(thumbnail_path):
                    os.remove(thumbnail_path)
            except Exception as e:
                print(f"Error deleting file: {e}")
        
        conn.close()
        return jsonify({'success': True})

# Additional routes (continuing with the rest of your routes...)
@app.route('/api/tasks/<int:task_id>/media')
@login_required
def task_media(task_id):
    """Get media files for a specific task"""
    username = session['username']
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT id FROM users WHERE username = ?', (username,))
    user_row = c.fetchone()
    if not user_row:
        conn.close()
        return jsonify([])
    user_id = user_row['id']
    
    c.execute('SELECT * FROM media WHERE user_id = ? AND task_id = ? ORDER BY upload_date DESC', (user_id, task_id))
    media_files = []
    for row in c.fetchall():
        media_files.append({
            'id': row['id'],
            'filename': row['filename'],
            'original_filename': row['original_filename'],
            'url': url_for('static', filename=f'uploads/{row["filename"]}'),
            'is_video': is_video_file(row['filename']),
            'description': row['description']
        })
    
    conn.close()
    return jsonify(media_files)

@app.route('/api/all-tasks')
@login_required
def all_tasks_api():
    if session['username'] != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    conn = get_db()
    c = conn.cursor()
    c.execute('''SELECT tasks.*, users.username as user FROM tasks JOIN users ON tasks.user_id = users.id''')
    all_tasks = [dict(id=row['id'], title=row['title'], completed=bool(row['completed']), due_date=row['due_date'], user=row['user']) for row in c.fetchall()]
    conn.close()
    return jsonify(all_tasks)

@app.route('/tasks/<int:task_id>/gallery')
@login_required
def task_gallery(task_id):
    """Gallery view for a specific task"""
    username = session['username']
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT id FROM users WHERE username = ?', (username,))
    user_row = c.fetchone()
    if not user_row:
        conn.close()
        return redirect(url_for('dashboard'))
    user_id = user_row['id']
    
    # Get task details
    c.execute('SELECT * FROM tasks WHERE id = ? AND user_id = ?', (task_id, user_id))
    task = c.fetchone()
    if not task:
        conn.close()
        return redirect(url_for('dashboard'))
    
    conn.close()
    return render_template('task_gallery.html', 
                         username=session['username'], 
                         task=dict(task),
                         task_id=task_id)

# Completed Tasks Tab
@app.route('/completed-tasks')
@login_required
def completed_tasks():
    """Display completed tasks page"""
    return render_template('completed_tasks.html', username=session['username'])

@app.route('/api/completed-tasks')
@login_required
def completed_tasks_api():
    """Get completed tasks sorted by priority and due date"""
    username = session['username']
    conn = get_db()
    c = conn.cursor()
    
    try:
        c.execute('SELECT id FROM users WHERE username = ?', (username,))
        user_row = c.fetchone()
        if not user_row:
            conn.close()
            return jsonify({'success': False, 'error': 'User not found'}), 404
        user_id = user_row['id']
        
        # Get completed tasks with media count
        c.execute('''
            SELECT 
                t.*,
                COUNT(m.id) as media_count,
                MAX(m.upload_date) as latest_media_date
            FROM tasks t
            LEFT JOIN media m ON t.id = m.task_id
            WHERE t.user_id = ? AND t.completed = 1
            GROUP BY t.id
            ORDER BY 
                CASE t.priority 
                    WHEN 'high' THEN 1 
                    WHEN 'medium' THEN 2 
                    WHEN 'low' THEN 3 
                END,
                t.due_date DESC,
                t.id DESC
        ''', (user_id,))
        
        completed_tasks = []
        for row in c.fetchall():
            task_dict = dict(row)
            task_dict['completed'] = bool(task_dict['completed'])
            task_dict['media_count'] = task_dict['media_count'] or 0
            completed_tasks.append(task_dict)
        
        conn.close()
        return jsonify({'success': True, 'tasks': completed_tasks})
        
    except Exception as e:
        conn.close()
        print(f"Error loading completed tasks: {str(e)}")
        return jsonify({'success': False, 'error': f'Failed to load completed tasks: {str(e)}'}), 500

# Manual notification trigger route for testing
@app.route('/api/trigger-notifications', methods=['POST'])
@login_required
def trigger_notifications():
    """Manually trigger notification check (for testing)"""
    if notification_system:
        notification_system.check_and_send_notifications()
        return jsonify({'success': True, 'message': 'Notifications triggered'})
    return jsonify({'success': False, 'error': 'Notification system not available'})

@app.route('/api/export-tasks', methods=['POST'])
@login_required
def export_tasks():
    """Export selected tasks as a text report"""
    username = session['username']
    conn = get_db()
    c = conn.cursor()
    
    try:
        # Get user ID
        c.execute('SELECT id FROM users WHERE username = ?', (username,))
        user_row = c.fetchone()
        if not user_row:
            conn.close()
            return jsonify({'success': False, 'error': 'User not found'}), 404
        user_id = user_row['id']
        
        # Get task IDs from request
        data = request.get_json()
        task_ids = data.get('task_ids', [])
        
        if not task_ids:
            conn.close()
            return jsonify({'success': False, 'error': 'No tasks selected for export'}), 400
        
        # Get selected tasks with media count
        placeholders = ','.join(['?' for _ in task_ids])
        c.execute(f'''
            SELECT 
                t.*,
                COUNT(m.id) as media_count
            FROM tasks t
            LEFT JOIN media m ON t.id = m.task_id
            WHERE t.user_id = ? AND t.id IN ({placeholders})
            GROUP BY t.id
            ORDER BY 
                CASE t.priority 
                    WHEN 'high' THEN 1 
                    WHEN 'medium' THEN 2 
                    WHEN 'low' THEN 3 
                END,
                t.due_date ASC,
                t.id DESC
        ''', [user_id] + task_ids)
        
        tasks = []
        for row in c.fetchall():
            task_dict = dict(row)
            task_dict['completed'] = bool(task_dict['completed'])
            task_dict['media_count'] = task_dict['media_count'] or 0
            tasks.append(task_dict)
        
        if not tasks:
            conn.close()
            return jsonify({'success': False, 'error': 'No tasks found'}), 404
        
        # Generate text report
        report = generate_task_report(tasks, username)
        
        conn.close()
        return jsonify({
            'success': True,
            'report': report,
            'filename': f'task_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
        })
        
    except Exception as e:
        conn.close()
        print(f"Error exporting tasks: {str(e)}")
        return jsonify({'success': False, 'error': f'Failed to export tasks: {str(e)}'}), 500

# Persistent login on server start
@app.before_request
def load_persistent_session():
    if 'username' not in session:
        sess = load_session()
        if 'username' in sess:
            session['username'] = sess['username']
            session.permanent = True

def initialize_app():
    """Initialize the application with notification system"""
    global notification_system
    try:
        # Import notification system here to avoid circular imports
        from notification_system import TaskNotificationSystem, add_notification_routes
        
        # Initialize notification system
        notification_system = TaskNotificationSystem(app, DB_FILE, BREVO_API_KEY)
        
        # Add notification routes
        add_notification_routes(app, notification_system)
        
        print("Notification system initialized successfully")
    except Exception as e:
        print(f"Warning: Could not initialize notification system: {e}")
        notification_system = None

@app.route('/api/media/<int:media_id>', methods=['PUT'])
@login_required
def update_media(media_id):
    username = session['username']
    conn = get_db()
    c = conn.cursor()
    
    try:
        # Get user ID
        c.execute('SELECT id FROM users WHERE username = ?', (username,))
        user_row = c.fetchone()
        if not user_row:
            conn.close()
            return jsonify({'success': False, 'error': 'User not found'}), 404
        user_id = user_row['id']
        
        # Get the request data
        data = request.get_json()
        
        # Check if media exists and belongs to user
        c.execute('SELECT * FROM media WHERE id = ? AND user_id = ?', (media_id, user_id))
        media_row = c.fetchone()
        if not media_row:
            conn.close()
            return jsonify({'success': False, 'error': 'Media not found'}), 404
        
        # Update task_id if provided
        if 'task_id' in data:
            task_id = data['task_id']
            c.execute('UPDATE media SET task_id = ? WHERE id = ? AND user_id = ?', 
                     (task_id, media_id, user_id))
            conn.commit()
            
            # Get updated media record
            c.execute('SELECT * FROM media WHERE id = ?', (media_id,))
            updated_row = c.fetchone()
            
            media = {
                'id': updated_row['id'],
                'filename': updated_row['filename'],
                'original_filename': updated_row['original_filename'],
                'file_type': updated_row['file_type'],
                'file_size': updated_row['file_size'],
                'upload_date': updated_row['upload_date'],
                'description': updated_row['description'],
                'task_id': updated_row['task_id'],
                'url': url_for('static', filename=f'uploads/{updated_row["filename"]}'),
                'is_video': is_video_file(updated_row['filename'])
            }
            
            conn.close()
            return jsonify({'success': True, 'media': media})
        
        conn.close()
        return jsonify({'success': False, 'error': 'No valid fields to update'})
        
    except Exception as e:
        conn.close()
        print(f"Error updating media: {str(e)}")
        return jsonify({'success': False, 'error': f'Failed to update media: {str(e)}'}), 500

@app.route('/api/media/<int:media_id>', methods=['DELETE'])
@login_required  
def delete_media_api(media_id):
    username = session['username']
    conn = get_db()
    c = conn.cursor()
    
    try:
        # Get user ID
        c.execute('SELECT id FROM users WHERE username = ?', (username,))
        user_row = c.fetchone()
        if not user_row:
            conn.close()
            return jsonify({'success': False, 'error': 'User not found'}), 404
        user_id = user_row['id']
        
        # Check if media exists and belongs to user
        c.execute('SELECT filename FROM media WHERE id = ? AND user_id = ?', (media_id, user_id))
        media_row = c.fetchone()
        if not media_row:
            conn.close()
            return jsonify({'success': False, 'error': 'Media not found'}), 404
        
        filename = media_row['filename']
        
        # Delete from database
        c.execute('DELETE FROM media WHERE id = ? AND user_id = ?', (media_id, user_id))
        conn.commit()
        
        # Delete file from filesystem
        try:
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            if os.path.exists(filepath):
                os.remove(filepath)
            
            # Delete thumbnail if exists
            thumbnail_filename = f"thumb_{filename}"
            thumbnail_path = os.path.join(app.config['UPLOAD_FOLDER'], thumbnail_filename)
            if os.path.exists(thumbnail_path):
                os.remove(thumbnail_path)
        except Exception as file_error:
            print(f"Error deleting media file: {file_error}")
        
        conn.close()
        return jsonify({'success': True, 'message': 'Media deleted successfully'})
        
    except Exception as e:
        conn.close()
        print(f"Error deleting media: {str(e)}")
        return jsonify({'success': False, 'error': f'Failed to delete media: {str(e)}'}), 500

# Initialize database on startup
init_db()

# Initialize the app with notification system
initialize_app()

if __name__ == '__main__':
    app.run(debug=True)