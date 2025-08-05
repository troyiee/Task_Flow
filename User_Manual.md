# Task Scheduler System - User Manual

**Document Version:** 1.0  
**Date:** December 2024  
**Project:** Task Scheduler Capstone Final System  

---

## Table of Contents

1. [Getting Started](#1-getting-started)
2. [User Registration and Login](#2-user-registration-and-login)
3. [Dashboard Overview](#3-dashboard-overview)
4. [Task Management](#4-task-management)
5. [Media Management](#5-media-management)
6. [Notification System](#6-notification-system)
7. [Analytics and Reports](#7-analytics-and-reports)
8. [Troubleshooting](#8-troubleshooting)

---

## 1. Getting Started

### 1.1 System Requirements
- **Web Browser:** Chrome 80+, Firefox 75+, Safari 13+, Edge 80+
- **Internet Connection:** Required for email notifications
- **JavaScript:** Must be enabled in your browser
- **Screen Resolution:** Minimum 1024x768 recommended

### 1.2 Accessing the System
1. Open your web browser
2. Navigate to the Task Scheduler application URL
3. You will be redirected to the login page if not already authenticated

---

## 2. User Registration and Login

### 2.1 Creating a New Account

#### Step 1: Access Registration
1. On the login page, click "Register" or "Create Account"
2. Fill in the registration form:
   - **Username:** Enter a unique username (3-20 characters)
   - **Email:** Enter a valid email address
   - **Password:** Create a strong password (minimum 6 characters)
3. Click "Register"

#### Step 2: Email Verification
1. Check your email for a 6-digit verification code (OTP)
2. Enter the code in the verification page
3. Click "Verify" to complete registration
4. If you don't receive the email, click "Resend OTP"

**Note:** The verification code expires after 10 minutes

### 2.2 Logging In
1. Enter your username and password
2. Click "Login"
3. You will be redirected to the dashboard
4. Your session remains active for 7 days

### 2.3 Logging Out
1. Click "Logout" in the navigation menu
2. You will be redirected to the login page

---

## 3. Dashboard Overview

### 3.1 Dashboard Components
- **Navigation Menu:** Access to all system features
- **Quick Stats:** Summary of your task statistics
- **Recent Tasks:** List of your most recent tasks
- **Quick Actions:** Fast access to common functions

### 3.2 Quick Statistics
The dashboard displays:
- **Total Tasks:** Number of all tasks created
- **Completed Tasks:** Number of finished tasks
- **Pending Tasks:** Number of incomplete tasks
- **Overdue Tasks:** Number of tasks past due date
- **Completion Rate:** Percentage of completed tasks

---

## 4. Task Management

### 4.1 Creating a New Task

#### Step 1: Access Task Creation
1. From the dashboard, click "Add Task" or "Create New Task"
2. Fill in the task form:
   - **Task Title:** Enter a descriptive title (required)
   - **Priority:** Select Low, Medium, or High
   - **Due Date:** Select a due date (optional)
   - **Description:** Add detailed description (optional)
3. Click "Create Task"

### 4.2 Viewing Tasks
- Tasks are displayed in a list format
- Each task shows: title, priority, due date, and completion status
- Tasks are sorted by priority and due date by default

### 4.3 Editing Tasks
1. Click the "Edit" button next to any task
2. Modify the fields as needed
3. Click "Update Task" to save changes

### 4.4 Marking Tasks Complete
1. Click the checkbox next to the task, OR
2. Edit the task and check the "Completed" checkbox
3. Save the changes

### 4.5 Deleting Tasks
1. Click the "Delete" button next to the task
2. Confirm deletion in the dialog
3. The task and associated media will be permanently removed

**Warning:** Deleted tasks cannot be recovered

### 4.6 Task Filtering and Sorting
- **Filter Options:** All Tasks, Pending, Completed, Overdue
- **Sort Options:** Priority, Due Date, Creation Date, Title

---

## 5. Media Management

### 5.1 Uploading Media Files

#### Step 1: Access Media Upload
1. Navigate to the Gallery section
2. Click "Upload Media" or "Add Files"

#### Step 2: Select and Upload Files
1. Click "Choose Files" or drag files to upload
2. **Supported Formats:**
   - Images: PNG, JPG, JPEG, GIF, BMP, WebP
   - Videos: MP4, AVI, MOV, WMV, FLV, WebM
3. **Maximum Size:** 50MB per file
4. Add optional description
5. Click "Upload"

### 5.2 Viewing Media Gallery
- Media files are displayed in a grid format
- Thumbnails are automatically generated for images
- Click on files to view full-size images or play videos

### 5.3 Associating Media with Tasks
1. During task creation, upload media files, OR
2. From Gallery, select a file and click "Associate with Task"
3. Choose the target task from the dropdown
4. Click "Save Association"

### 5.4 Deleting Media Files
1. Find the file in the Gallery
2. Click the "Delete" button
3. Confirm deletion

**Warning:** Deleted files cannot be recovered

---

## 6. Notification System

### 6.1 Configuring Notifications
1. Go to Settings → Notification Preferences
2. Configure:
   - Email Notifications (enable/disable)
   - Due Today Alerts
   - Due Tomorrow Alerts
   - Overdue Alerts
   - Reminder Hours
3. Click "Save Settings"

### 6.2 Email Notifications
- **Types:** Due Today, Due Tomorrow, Overdue, Task Completion
- **Content:** Task details, due date, priority, direct links
- **Frequency:** Based on your preferences and task due dates

### 6.3 In-App Notifications
1. Click the notification bell icon
2. View recent notifications
3. Mark notifications as read
4. Access related tasks directly

---

## 7. Analytics and Reports

### 7.1 Viewing Statistics
- **Dashboard Stats:** Real-time task metrics
- **Detailed Analytics:** Comprehensive task analysis
- **Productivity Trends:** Performance over time

### 7.2 Generating Reports
1. Go to Analytics section
2. Select report type:
   - Task Summary
   - Completion Report
   - Productivity Report
   - Media Usage Report
3. Set parameters (date range, filters)
4. Click "Generate"

### 7.3 Exporting Data
- **Formats:** PDF, CSV, JSON
- **Process:** Generate report → Click Export → Choose format → Download

---

## 8. Troubleshooting

### 8.1 Common Issues

#### Login Problems
- Check Caps Lock is off
- Clear browser cache and cookies
- Try a different browser
- Reset password if needed

#### File Upload Issues
- Check file size (max 50MB)
- Verify file type is supported
- Check internet connection
- Try uploading one file at a time

#### Email Notifications Not Working
- Check notification preferences are enabled
- Verify email address is correct
- Check spam/junk folder
- Contact system administrator

#### Task Not Saving
- Check internet connection
- Refresh the page
- Try creating the task again
- Clear browser cache

### 8.2 Error Messages

#### "Invalid Credentials"
- Username or password is incorrect
- Check spelling and case sensitivity

#### "File Type Not Supported"
- Upload only supported file formats
- Convert files to supported format

#### "Session Expired"
- Log in again
- Session may have timed out

#### "Database Error"
- Refresh the page
- Try again in a few minutes
- Contact system administrator if persistent

### 8.3 Performance Issues

#### Slow Loading
- Check internet connection
- Clear browser cache
- Close unnecessary browser tabs
- Try a different browser

#### Large File Uploads
- Compress files before uploading
- Upload during off-peak hours
- Use wired internet connection
- Break large uploads into smaller files

---

## Frequently Asked Questions

### Account Management
**Q: Can I change my username?**
A: No, usernames cannot be changed after registration.

**Q: How do I reset my password?**
A: Contact the system administrator.

**Q: Can I use the same email for multiple accounts?**
A: No, each email address can only be used for one account.

### Task Management
**Q: Can I recover deleted tasks?**
A: No, deleted tasks cannot be recovered.

**Q: How many tasks can I create?**
A: There is no limit on the number of tasks.

**Q: Can I assign tasks to other users?**
A: Currently, tasks are personal and cannot be assigned to others.

### Media Management
**Q: What file types are supported?**
A: Images (PNG, JPG, GIF, BMP, WebP) and videos (MP4, AVI, MOV, WMV, FLV, WebM).

**Q: What is the maximum file size?**
A: 50MB per file.

### Notifications
**Q: How often are email notifications sent?**
A: Based on your preferences and task due dates.

**Q: Can I disable all notifications?**
A: Yes, you can disable email notifications in preferences.

### System Usage
**Q: Can I access the system from mobile devices?**
A: Yes, the system is responsive and works on mobile browsers.

**Q: Is my data secure?**
A: Yes, all data is encrypted and stored securely.

**Q: How long is my session active?**
A: Sessions remain active for 7 days unless you log out.

---

## Contact Information

For technical support or questions not covered in this manual:

- **Email:** [Support Email]
- **System Administrator:** [Admin Contact]
- **Documentation Version:** 1.0
- **Last Updated:** December 2024

---

**Document End**

*This user manual provides comprehensive guidance for using the Task Scheduler System. For the most up-to-date information, please refer to the system's help section or contact the system administrator.* 