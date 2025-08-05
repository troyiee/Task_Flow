# notification_system.py - Enhanced Task Notification System
import sqlite3
import json
import os
import schedule
import time
import threading
from datetime import datetime, timedelta, date
from flask import Flask, jsonify, request, session
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException


class TaskNotificationSystem:
    def __init__(self, app, db_file='app.db', brevo_api_key=None):
        self.app = app
        self.db_file = db_file
        self.brevo_api_key = brevo_api_key
        self.notification_log = []
        self.user_preferences = {}
        
        # Initialize notification preferences
        self.init_notification_tables()
        
        # Start background scheduler
        self.start_scheduler()
    
    def init_notification_tables(self):
        """Initialize notification-related database tables"""
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        
        # Notification preferences table
        c.execute('''CREATE TABLE IF NOT EXISTS notification_preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            email_enabled INTEGER DEFAULT 1,
            due_today_enabled INTEGER DEFAULT 1,
            due_tomorrow_enabled INTEGER DEFAULT 1,
            overdue_enabled INTEGER DEFAULT 1,
            reminder_hours INTEGER DEFAULT 24,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )''')
        
        # Notification log table
        c.execute('''CREATE TABLE IF NOT EXISTS notification_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            task_id INTEGER NOT NULL,
            notification_type TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            sent_at TIMESTAMP,
            error_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (task_id) REFERENCES tasks (id)
        )''')
        
        # In-app notifications table
        c.execute('''CREATE TABLE IF NOT EXISTS in_app_notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            type TEXT DEFAULT 'info',
            read_status INTEGER DEFAULT 0,
            task_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (task_id) REFERENCES tasks (id)
        )''')
        
        conn.commit()
        conn.close()
    
    def get_user_preferences(self, user_id):
        """Get notification preferences for a user"""
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        c.execute('SELECT * FROM notification_preferences WHERE user_id = ?', (user_id,))
        prefs = c.fetchone()
        
        if not prefs:
            # Create default preferences
            c.execute('''INSERT INTO notification_preferences 
                        (user_id, email_enabled, due_today_enabled, due_tomorrow_enabled, overdue_enabled, reminder_hours) 
                        VALUES (?, 1, 1, 1, 1, 24)''', (user_id,))
            conn.commit()
            
            c.execute('SELECT * FROM notification_preferences WHERE user_id = ?', (user_id,))
            prefs = c.fetchone()
        
        conn.close()
        return dict(prefs) if prefs else None
    
    def send_immediate_task_notification(self, user_id, username, email, task_data, notification_type):
        """Send immediate notification for a single task"""
        try:
            # Check user preferences
            prefs = self.get_user_preferences(user_id)
            if not prefs or not prefs.get('email_enabled', 1):
                print(f"Email notifications disabled for user {username}")
                return False
            
            # Check specific notification type preference
            if notification_type == 'due_today' and not prefs.get('due_today_enabled', 1):
                return False
            elif notification_type == 'due_tomorrow' and not prefs.get('due_tomorrow_enabled', 1):
                return False
            elif notification_type == 'overdue' and not prefs.get('overdue_enabled', 1):
                return False
            
            # Send email notification
            success = self.send_email_notification(
                email, username, [task_data], notification_type
            )
            
            # Log notification attempt
            self.log_notification(
                user_id, 
                task_data['id'], 
                f"immediate_{notification_type}",
                'sent' if success else 'failed',
                None if success else 'Email sending failed'
            )
            
            # Create in-app notification
            if notification_type == 'due_today':
                title = "🚨 New Task Due Today"
                message = f'Task "{task_data["title"]}" is due today!'
            elif notification_type == 'due_tomorrow':
                title = "⏰ New Task Due Tomorrow"
                message = f'Task "{task_data["title"]}" is due tomorrow!'
            elif notification_type == 'overdue':
                title = "❗ New Overdue Task"
                message = f'Task "{task_data["title"]}" is already overdue!'
            
            self.create_in_app_notification(
                user_id, 
                title, 
                message, 
                'warning' if notification_type == 'overdue' else 'info',
                task_data['id']
            )
            
            print(f"Immediate {notification_type} notification sent for task: {task_data['title']}")
            return success
            
        except Exception as e:
            print(f"Error sending immediate notification: {e}")
            self.log_notification(
                user_id, 
                task_data['id'], 
                f"immediate_{notification_type}",
                'failed',
                str(e)
            )
            return False

    def check_all_users_tasks(self):
        """Enhanced method to check all users' tasks and send notifications"""
        print(f"Checking all users' tasks at {datetime.now()}")
        
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        # Get all users with their incomplete tasks
        c.execute('''
            SELECT DISTINCT u.id, u.username, u.email
            FROM users u
            INNER JOIN tasks t ON u.id = t.user_id
            WHERE t.completed = 0 AND t.due_date IS NOT NULL
        ''')
        
        users = c.fetchall()
        conn.close()
        
        for user in users:
            try:
                # Get user's due tasks
                due_today_tasks = self.get_user_due_tasks(user['id'], 'due_today')
                due_tomorrow_tasks = self.get_user_due_tasks(user['id'], 'due_tomorrow')
                overdue_tasks = self.get_user_due_tasks(user['id'], 'overdue')
                
                # Send notifications for each category
                if due_today_tasks:
                    self.send_user_notification_batch(user, due_today_tasks, 'due_today')
                
                if due_tomorrow_tasks:
                    self.send_user_notification_batch(user, due_tomorrow_tasks, 'due_tomorrow')
                
                if overdue_tasks:
                    self.send_user_notification_batch(user, overdue_tasks, 'overdue')
                    
            except Exception as e:
                print(f"Error processing notifications for user {user['username']}: {e}")

    def get_user_due_tasks(self, user_id, notification_type):
        """Get due tasks for a specific user"""
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        today = date.today()
        tomorrow = today + timedelta(days=1)
        
        if notification_type == 'due_today':
            c.execute('''SELECT * FROM tasks 
                        WHERE user_id = ? AND due_date = ? AND completed = 0''',
                     (user_id, today.strftime('%Y-%m-%d')))
        elif notification_type == 'due_tomorrow':
            c.execute('''SELECT * FROM tasks 
                        WHERE user_id = ? AND due_date = ? AND completed = 0''',
                     (user_id, tomorrow.strftime('%Y-%m-%d')))
        elif notification_type == 'overdue':
            c.execute('''SELECT * FROM tasks 
                        WHERE user_id = ? AND due_date < ? AND completed = 0''',
                     (user_id, today.strftime('%Y-%m-%d')))
        
        tasks = c.fetchall()
        conn.close()
        
        return [dict(task) for task in tasks]

    def send_user_notification_batch(self, user, tasks, notification_type):
        """Send notification batch for a user"""
        try:
            # Check user preferences
            prefs = self.get_user_preferences(user['id'])
            if not prefs or not prefs.get('email_enabled', 1):
                return False
            
            # Check specific notification type preference
            if notification_type == 'due_today' and not prefs.get('due_today_enabled', 1):
                return False
            elif notification_type == 'due_tomorrow' and not prefs.get('due_tomorrow_enabled', 1):
                return False
            elif notification_type == 'overdue' and not prefs.get('overdue_enabled', 1):
                return False
            
            # Check if we already sent notifications for these tasks today
            if self.already_notified_today(user['id'], [task['id'] for task in tasks], notification_type):
                print(f"Already notified user {user['username']} about {notification_type} tasks today")
                return False
            
            # Send email notification
            success = self.send_email_notification(
                user['email'], user['username'], tasks, notification_type
            )
            
            # Log notification attempts
            for task in tasks:
                self.log_notification(
                    user['id'], 
                    task['id'], 
                    notification_type,
                    'sent' if success else 'failed',
                    None if success else 'Email sending failed'
                )
            
            # Create in-app notification
            task_count = len(tasks)
            if notification_type == 'due_today':
                title = f"🚨 {task_count} Task{'s' if task_count != 1 else ''} Due Today"
                message = f"You have {task_count} task{'s' if task_count != 1 else ''} due today!"
            elif notification_type == 'due_tomorrow':
                title = f"⏰ {task_count} Task{'s' if task_count != 1 else ''} Due Tomorrow"
                message = f"You have {task_count} task{'s' if task_count != 1 else ''} due tomorrow!"
            elif notification_type == 'overdue':
                title = f"❗ {task_count} Overdue Task{'s' if task_count != 1 else ''}"
                message = f"You have {task_count} overdue task{'s' if task_count != 1 else ''}!"
            
            self.create_in_app_notification(
                user['id'], 
                title, 
                message, 
                'warning' if notification_type == 'overdue' else 'info'
            )
            
            print(f"Batch {notification_type} notifications sent to {user['username']}")
            return success
            
        except Exception as e:
            print(f"Error sending batch notification: {e}")
            return False

    def already_notified_today(self, user_id, task_ids, notification_type):
        """Check if we already sent notifications for these tasks today"""
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        
        today = date.today().strftime('%Y-%m-%d')
        
        placeholders = ','.join(['?' for _ in task_ids])
        query = f'''SELECT COUNT(*) as count FROM notification_log 
                   WHERE user_id = ? AND task_id IN ({placeholders}) 
                   AND notification_type = ? AND status = 'sent' 
                   AND DATE(sent_at) = ?'''
        
        params = [user_id] + task_ids + [notification_type, today]
        c.execute(query, params)
        
        count = c.fetchone()[0]
        conn.close()
        
        return count > 0
    
    def update_user_preferences(self, user_id, preferences):
        """Update notification preferences for a user"""
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        
        c.execute('''UPDATE notification_preferences 
                    SET email_enabled = ?, due_today_enabled = ?, due_tomorrow_enabled = ?, 
                        overdue_enabled = ?, reminder_hours = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ?''', 
                  (preferences.get('email_enabled', 1),
                   preferences.get('due_today_enabled', 1),
                   preferences.get('due_tomorrow_enabled', 1),
                   preferences.get('overdue_enabled', 1),
                   preferences.get('reminder_hours', 24),
                   user_id))
        
        conn.commit()
        conn.close()
    
    def get_due_tasks(self, notification_type='due_today'):
        """Get tasks that are due based on notification type"""
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        today = date.today()
        tomorrow = today + timedelta(days=1)
        
        if notification_type == 'due_today':
            query = '''SELECT t.*, u.username, u.email, np.* 
                      FROM tasks t 
                      JOIN users u ON t.user_id = u.id 
                      LEFT JOIN notification_preferences np ON u.id = np.user_id
                      WHERE t.due_date = ? AND t.completed = 0 AND (np.due_today_enabled = 1 OR np.due_today_enabled IS NULL)'''
            params = (today.strftime('%Y-%m-%d'),)
            
        elif notification_type == 'due_tomorrow':
            query = '''SELECT t.*, u.username, u.email, np.* 
                      FROM tasks t 
                      JOIN users u ON t.user_id = u.id 
                      LEFT JOIN notification_preferences np ON u.id = np.user_id
                      WHERE t.due_date = ? AND t.completed = 0 AND (np.due_tomorrow_enabled = 1 OR np.due_tomorrow_enabled IS NULL)'''
            params = (tomorrow.strftime('%Y-%m-%d'),)
            
        elif notification_type == 'overdue':
            query = '''SELECT t.*, u.username, u.email, np.* 
                      FROM tasks t 
                      JOIN users u ON t.user_id = u.id 
                      LEFT JOIN notification_preferences np ON u.id = np.user_id
                      WHERE t.due_date < ? AND t.completed = 0 AND (np.overdue_enabled = 1 OR np.overdue_enabled IS NULL)'''
            params = (today.strftime('%Y-%m-%d'),)
        
        c.execute(query, params)
        tasks = c.fetchall()
        conn.close()
        
        return [dict(task) for task in tasks]
    
    def send_email_notification(self, to_email, username, tasks, notification_type):
        """Send email notification using Brevo API"""
        if not self.brevo_api_key:
            print("Brevo API key not configured")
            return False
        
        try:
            configuration = sib_api_v3_sdk.Configuration()
            configuration.api_key['api-key'] = self.brevo_api_key
            api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))

            # Generate email content based on notification type
            subject, html_content = self.generate_email_content(username, tasks, notification_type)
            
            sender = {"name": "TaskFlow Scheduler", "email": "garciaraffitroy08@gmail.com"}
            to = [{"email": to_email}]

            send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
                to=to,
                html_content=html_content,
                sender=sender,
                subject=subject
            )

            api_response = api_instance.send_transac_email(send_smtp_email)
            print(f"Notification email sent to {to_email}. Message ID: {api_response}")
            return True
            
        except ApiException as e:
            print(f"Brevo API Error: {e}")
            return False
        except Exception as e:
            print(f"General error sending notification: {e}")
            return False
    
    def generate_email_content(self, username, tasks, notification_type):
        """Generate email content based on notification type"""
        if notification_type == 'due_today':
            subject = f"🚨 Tasks Due Today - {len(tasks)} Task{'s' if len(tasks) != 1 else ''}"
            title = "Tasks Due Today"
            message = f"Hi {username}, you have {len(tasks)} task{'s' if len(tasks) != 1 else ''} due today:"
            
        elif notification_type == 'due_tomorrow':
            subject = f"⏰ Tasks Due Tomorrow - {len(tasks)} Task{'s' if len(tasks) != 1 else ''}"
            title = "Tasks Due Tomorrow"
            message = f"Hi {username}, you have {len(tasks)} task{'s' if len(tasks) != 1 else ''} due tomorrow:"
            
        elif notification_type == 'overdue':
            subject = f"❗ Overdue Tasks - {len(tasks)} Task{'s' if len(tasks) != 1 else ''}"
            title = "Overdue Tasks"
            message = f"Hi {username}, you have {len(tasks)} overdue task{'s' if len(tasks) != 1 else ''}:"
        
        # Priority colors
        priority_colors = {
            'low': '#4facfe',
            'medium': '#43e97b', 
            'high': '#fa709a'
        }
        
        # Generate task list HTML
        task_list_html = ""
        for task in tasks:
            priority_color = priority_colors.get(task['priority'], '#6b7280')
            due_date = datetime.strptime(task['due_date'], '%Y-%m-%d').strftime('%B %d, %Y')
            
            task_list_html += f"""
            <div style="background: #f8fafc; border-left: 4px solid {priority_color}; padding: 16px; margin: 12px 0; border-radius: 8px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <h4 style="margin: 0; color: #1f2937; font-size: 16px;">{task['title']}</h4>
                    <span style="background: {priority_color}; color: white; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 500;">
                        {task['priority'].title()} Priority
                    </span>
                </div>
                <p style="margin: 0; color: #6b7280; font-size: 14px;">
                    <strong>Due:</strong> {due_date}
                </p>
            </div>
            """
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{title}</title>
        </head>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 16px; text-align: center; margin-bottom: 30px;">
                <h1 style="margin: 0; font-size: 28px; font-weight: 700;">📋 TaskFlow</h1>
                <h2 style="margin: 10px 0 0 0; font-size: 20px; font-weight: 400; opacity: 0.9;">{title}</h2>
            </div>
            
            <div style="background: white; padding: 30px; border-radius: 16px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                <p style="font-size: 16px; margin-bottom: 24px;">{message}</p>
                
                {task_list_html}
                
                <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #e5e7eb;">
                    <p style="margin: 0; color: #6b7280; font-size: 14px; text-align: center;">
                        Stay organized and productive with TaskFlow! 
                        <br>
                        <a href="#" style="color: #667eea; text-decoration: none;">Manage your tasks →</a>
                    </p>
                </div>
            </div>
            
            <div style="text-align: center; margin-top: 20px; color: #6b7280; font-size: 12px;">
                <p>You're receiving this because you have notifications enabled for your TaskFlow account.</p>
                <p>© 2024 TaskFlow. All rights reserved.</p>
            </div>
            
        </body>
        </html>
        """
        
        return subject, html_content
    
    def create_in_app_notification(self, user_id, title, message, notification_type='info', task_id=None):
        """Create an in-app notification"""
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        
        c.execute('''INSERT INTO in_app_notifications 
                    (user_id, title, message, type, task_id) 
                    VALUES (?, ?, ?, ?, ?)''', 
                  (user_id, title, message, notification_type, task_id))
        
        conn.commit()
        conn.close()
    
    def log_notification(self, user_id, task_id, notification_type, status='sent', error_message=None):
        """Log notification attempt"""
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        
        c.execute('''INSERT INTO notification_log 
                    (user_id, task_id, notification_type, status, sent_at, error_message) 
                    VALUES (?, ?, ?, ?, ?, ?)''', 
                  (user_id, task_id, notification_type, status, 
                   datetime.now().strftime('%Y-%m-%d %H:%M:%S') if status == 'sent' else None,
                   error_message))
        
        conn.commit()
        conn.close()
    
    def process_notifications(self, notification_type):
        """Process notifications for a specific type"""
        print(f"Processing {notification_type} notifications...")
        
        due_tasks = self.get_due_tasks(notification_type)
        
        # Group tasks by user
        user_tasks = {}
        for task in due_tasks:
            user_id = task['user_id']
            if user_id not in user_tasks:
                user_tasks[user_id] = {
                    'username': task['username'],
                    'email': task['email'],
                    'tasks': []
                }
            user_tasks[user_id]['tasks'].append(task)
        
        # Send notifications to each user
        for user_id, user_data in user_tasks.items():
            try:
                # Check if user has email notifications enabled
                prefs = self.get_user_preferences(user_id)
                if prefs and prefs.get('email_enabled', 1):
                    # Send email notification
                    success = self.send_email_notification(
                        user_data['email'],
                        user_data['username'],
                        user_data['tasks'],
                        notification_type
                    )
                    
                    # Log notification attempts
                    for task in user_data['tasks']:
                        self.log_notification(
                            user_id, 
                            task['id'], 
                            notification_type,
                            'sent' if success else 'failed',
                            None if success else 'Email sending failed'
                        )
                
                # Create in-app notifications
                task_count = len(user_data['tasks'])
                if notification_type == 'due_today':
                    title = f"🚨 {task_count} Task{'s' if task_count != 1 else ''} Due Today"
                    message = f"You have {task_count} task{'s' if task_count != 1 else ''} due today. Don't forget to complete them!"
                elif notification_type == 'due_tomorrow':
                    title = f"⏰ {task_count} Task{'s' if task_count != 1 else ''} Due Tomorrow"
                    message = f"You have {task_count} task{'s' if task_count != 1 else ''} due tomorrow. Start planning!"
                elif notification_type == 'overdue':
                    title = f"❗ {task_count} Overdue Task{'s' if task_count != 1 else ''}"
                    message = f"You have {task_count} overdue task{'s' if task_count != 1 else ''}. Please complete them as soon as possible!"
                
                self.create_in_app_notification(
                    user_id, 
                    title, 
                    message, 
                    'warning' if notification_type == 'overdue' else 'info'
                )
                
                print(f"Notifications sent to user {user_data['username']} ({user_data['email']})")
                
            except Exception as e:
                print(f"Error sending notifications to user {user_id}: {e}")
                # Log failed notifications
                for task in user_data['tasks']:
                    self.log_notification(
                        user_id, 
                        task['id'], 
                        notification_type,
                        'failed',
                        str(e)
                    )
    
    def check_and_send_notifications(self):
        """Enhanced method to check for due tasks and send notifications"""
        print(f"Enhanced notification check at {datetime.now()}")
        self.check_all_users_tasks()
        print("Enhanced notification check completed")
    
    def start_scheduler(self):
        """Start the enhanced background scheduler"""
        # Schedule notifications multiple times per day
        schedule.every().day.at("08:00").do(self.check_all_users_tasks)  # Morning
        schedule.every().day.at("12:00").do(self.check_all_users_tasks)  # Noon
        schedule.every().day.at("17:00").do(self.check_all_users_tasks)  # Evening
        schedule.every().day.at("20:00").do(self.check_all_users_tasks)  # Night
        
        # Start scheduler in a separate thread
        def run_scheduler():
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
        print("Enhanced notification scheduler started with multiple daily checks")
    
    def get_user_notifications(self, user_id, limit=10, include_read=False):
        """Get in-app notifications for a user"""
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        query = '''SELECT * FROM in_app_notifications 
                  WHERE user_id = ?'''
        params = [user_id]
        
        if not include_read:
            query += ' AND read_status = 0'
        
        query += ' ORDER BY created_at DESC LIMIT ?'
        params.append(limit)
        
        c.execute(query, params)
        notifications = c.fetchall()
        conn.close()
        
        return [dict(notification) for notification in notifications]
    
    def mark_notification_read(self, notification_id, user_id):
        """Mark a notification as read"""
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        
        c.execute('''UPDATE in_app_notifications 
                    SET read_status = 1 
                    WHERE id = ? AND user_id = ?''', 
                  (notification_id, user_id))
        
        conn.commit()
        conn.close()
    
    def get_notification_stats(self, user_id):
        """Get notification statistics for a user"""
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        # Get unread count
        c.execute('SELECT COUNT(*) as unread_count FROM in_app_notifications WHERE user_id = ? AND read_status = 0', (user_id,))
        unread_count = c.fetchone()['unread_count']
        
        # Get recent notification log
        c.execute('''SELECT COUNT(*) as total_sent FROM notification_log 
                    WHERE user_id = ? AND status = "sent" AND sent_at >= date('now', '-7 days')''', (user_id,))
        recent_sent = c.fetchone()['total_sent']
        
        conn.close()
        
        return {
            'unread_count': unread_count,
            'recent_sent': recent_sent
        }

# Flask routes for notification management
def add_notification_routes(app, notification_system):
    """Add notification-related routes to Flask app"""
    
    @app.route('/api/notifications', methods=['GET'])
    def get_notifications():
        """Get user notifications"""
        if 'username' not in request.args and 'username' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        
        username = request.args.get('username') or session.get('username')
        
        # Get user ID
        conn = sqlite3.connect(notification_system.db_file)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute('SELECT id FROM users WHERE username = ?', (username,))
        user = c.fetchone()
        conn.close()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        user_id = user['id']
        limit = request.args.get('limit', 10, type=int)
        include_read = request.args.get('include_read', 'false').lower() == 'true'
        
        notifications = notification_system.get_user_notifications(user_id, limit, include_read)
        stats = notification_system.get_notification_stats(user_id)
        
        return jsonify({
            'success': True,
            'notifications': notifications,
            'stats': stats
        })
    
    @app.route('/api/notifications/<int:notification_id>/mark-read', methods=['POST'])
    def mark_notification_read(notification_id):
        """Mark a notification as read"""
        if 'username' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        
        username = session['username']
        
        # Get user ID
        conn = sqlite3.connect(notification_system.db_file)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute('SELECT id FROM users WHERE username = ?', (username,))
        user = c.fetchone()
        conn.close()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        user_id = user['id']
        notification_system.mark_notification_read(notification_id, user_id)
        
        return jsonify({'success': True})
    
    @app.route('/api/notification-preferences', methods=['GET', 'POST'])
    def notification_preferences():
        """Get or update notification preferences"""
        if 'username' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        
        username = session['username']
        
        # Get user ID
        conn = sqlite3.connect(notification_system.db_file)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute('SELECT id FROM users WHERE username = ?', (username,))
        user = c.fetchone()
        conn.close()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        user_id = user['id']
        
        if request.method == 'GET':
            preferences = notification_system.get_user_preferences(user_id)
            return jsonify({'success': True, 'preferences': preferences})
        
        elif request.method == 'POST':
            preferences = request.get_json()
            notification_system.update_user_preferences(user_id, preferences)
            return jsonify({'success': True, 'message': 'Preferences updated'})
    
    @app.route('/api/test-notification', methods=['POST'])
    def test_notification():
        """Send a test notification (for development)"""
        if 'username' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        
        notification_system.check_and_send_notifications()
        return jsonify({'success': True, 'message': 'Test notifications sent'})

# Usage example:
def setup_notification_system(app, brevo_api_key):
    """Setup the notification system with your Flask app"""
    notification_system = TaskNotificationSystem(
        app=app,
        db_file='app.db',
        brevo_api_key=brevo_api_key
    )
    
    # Add notification routes
    add_notification_routes(app, notification_system)
    
    return notification_system