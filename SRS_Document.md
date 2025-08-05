# Software Requirements Specification (SRS)
## Task Scheduler System

**Document Version:** 1.0  
**Date:** December 2024  
**Project:** Task Scheduler Capstone Final System  
**Prepared By:** Development Team  

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Overall Description](#2-overall-description)
3. [Specific Requirements](#3-specific-requirements)
4. [External Interface Requirements](#4-external-interface-requirements)
5. [Performance Requirements](#5-performance-requirements)
6. [Design Constraints](#6-design-constraints)
7. [Software System Attributes](#7-software-system-attributes)
8. [Appendices](#8-appendices)

---

## 1. Introduction

### 1.1 Purpose
This Software Requirements Specification (SRS) document describes the functional and non-functional requirements for the Task Scheduler System, a web-based application designed to help users manage their tasks efficiently with features including task creation, prioritization, due date management, media attachments, and automated notifications.

### 1.2 Scope
The Task Scheduler System is a Flask-based web application that provides:
- User authentication and account management
- Task creation, editing, and deletion
- Task prioritization and due date management
- Media file upload and management
- Automated email notifications
- Progress tracking and statistics
- Gallery view for media files
- In-app notification system

### 1.3 Definitions, Acronyms, and Abbreviations
- **SRS**: Software Requirements Specification
- **API**: Application Programming Interface
- **OTP**: One-Time Password
- **UI**: User Interface
- **UX**: User Experience
- **SQLite**: Lightweight database engine
- **Flask**: Python web framework
- **Brevo**: Email service provider (formerly Sendinblue)

### 1.4 References
- Flask Documentation: https://flask.palletsprojects.com/
- SQLite Documentation: https://www.sqlite.org/docs.html
- Brevo API Documentation: https://developers.brevo.com/

### 1.5 Overview
The remainder of this document is organized as follows:
- Section 2 provides an overall description of the system
- Section 3 details specific functional and non-functional requirements
- Section 4 describes external interface requirements
- Section 5 outlines performance requirements
- Section 6 lists design constraints
- Section 7 covers software system attributes
- Section 8 contains appendices with additional information

---

## 2. Overall Description

### 2.1 Product Perspective
The Task Scheduler System is a standalone web application built using the Flask framework. It operates as a client-server architecture where:
- **Backend**: Python Flask application with SQLite database
- **Frontend**: HTML/CSS/JavaScript web interface
- **External Services**: Brevo email service for notifications
- **File Storage**: Local file system for media uploads

### 2.2 Product Functions
The system provides the following core functions:

#### 2.2.1 User Management
- User registration with email verification
- User login/logout functionality
- Session management with persistent login
- Password hashing and security

#### 2.2.2 Task Management
- Create, read, update, and delete tasks
- Set task priorities (low, medium, high)
- Assign due dates to tasks
- Mark tasks as completed
- Task progress tracking

#### 2.2.3 Media Management
- Upload images, videos, and documents
- Automatic thumbnail generation for images
- Media file organization by task
- Gallery view for media files
- File type validation and size limits

#### 2.2.4 Notification System
- Automated email notifications for due tasks
- In-app notification system
- Configurable notification preferences
- Multiple notification types (due today, due tomorrow, overdue)

#### 2.2.5 Analytics and Reporting
- Task completion statistics
- Progress tracking
- Media usage analytics
- User activity monitoring

### 2.3 User Classes and Characteristics
The system serves the following user classes:

#### 2.3.1 Regular Users
- **Primary users** who create and manage tasks
- **Characteristics**: Need to organize tasks, set priorities, track progress
- **Technical Level**: Basic computer literacy
- **Access**: Full access to task management features

#### 2.3.2 Administrators
- **System administrators** with additional privileges
- **Characteristics**: Need to monitor system usage and manage users
- **Technical Level**: Advanced computer literacy
- **Access**: All regular user features plus administrative functions

### 2.4 Operating Environment
- **Operating System**: Cross-platform (Windows, macOS, Linux)
- **Web Browser**: Modern browsers (Chrome, Firefox, Safari, Edge)
- **Server**: Python 3.7+ with Flask framework
- **Database**: SQLite database engine
- **Email Service**: Brevo API integration

### 2.5 Design and Implementation Constraints
- **Technology Stack**: Flask, SQLite, HTML/CSS/JavaScript
- **File Storage**: Local file system with size limitations
- **Email Service**: Dependency on Brevo API
- **Security**: Basic authentication with password hashing
- **Scalability**: Single-server architecture

### 2.6 Assumptions and Dependencies
- Users have access to a modern web browser
- Internet connection required for email notifications
- Valid Brevo API key is configured
- Sufficient disk space for file uploads
- Python environment is properly configured

---

## 3. Specific Requirements

### 3.1 External Interface Requirements

#### 3.1.1 User Interfaces
The system shall provide the following user interfaces:

**3.1.1.1 Login/Registration Interface**
- Username and password input fields
- Email address input for registration
- OTP verification for new registrations
- Error message display for invalid credentials
- "Remember me" functionality

**3.1.1.2 Dashboard Interface**
- Overview of user's tasks
- Quick task creation form
- Task statistics and progress indicators
- Navigation to other system features
- User profile information

**3.1.1.3 Task Management Interface**
- Task list with sorting and filtering options
- Add new task form with title, priority, and due date
- Edit task functionality
- Delete task confirmation
- Task completion status toggle

**3.1.1.4 Media Gallery Interface**
- Grid view of uploaded media files
- Thumbnail generation for images
- Video playback support
- File upload interface with drag-and-drop
- Media file organization by task

**3.1.1.5 Notification Center**
- In-app notification display
- Notification preferences configuration
- Email notification settings
- Notification history and status

#### 3.1.2 Hardware Interfaces
- **Minimum Requirements**:
  - 2GB RAM
  - 1GB free disk space
  - Network connectivity for email notifications
- **Recommended Requirements**:
  - 4GB RAM
  - 5GB free disk space
  - High-speed internet connection

#### 3.1.3 Software Interfaces
- **Web Browser**: Chrome 80+, Firefox 75+, Safari 13+, Edge 80+
- **Python**: Version 3.7 or higher
- **Flask**: Version 3.0.3
- **SQLite**: Version 3.0 or higher
- **Brevo API**: Latest version for email services

#### 3.1.4 Communications Interfaces
- **HTTP/HTTPS**: For web application communication
- **SMTP**: For email notifications via Brevo API
- **REST API**: For programmatic access to system functions

### 3.2 Functional Requirements

#### 3.2.1 User Authentication and Management

**FR-001: User Registration**
- The system shall allow new users to register with username, email, and password
- The system shall validate email format and uniqueness
- The system shall send OTP verification email to new users
- The system shall require OTP verification before account activation
- The system shall hash passwords using secure algorithms

**FR-002: User Login**
- The system shall authenticate users with username and password
- The system shall maintain user sessions with persistent login
- The system shall redirect authenticated users to dashboard
- The system shall display appropriate error messages for failed login attempts

**FR-003: Session Management**
- The system shall maintain user sessions across browser sessions
- The system shall implement session timeout after 7 days of inactivity
- The system shall provide secure logout functionality
- The system shall protect routes requiring authentication

#### 3.2.2 Task Management

**FR-004: Task Creation**
- The system shall allow users to create new tasks with title, priority, and due date
- The system shall validate task title (required field)
- The system shall support priority levels: low, medium, high
- The system shall allow optional due date assignment
- The system shall automatically assign creation timestamp

**FR-005: Task Modification**
- The system shall allow users to edit existing tasks
- The system shall permit modification of title, priority, due date, and completion status
- The system shall validate all modified fields
- The system shall maintain task history and audit trail

**FR-006: Task Deletion**
- The system shall allow users to delete their own tasks
- The system shall require confirmation before task deletion
- The system shall remove associated media files when deleting tasks
- The system shall provide feedback on successful deletion

**FR-007: Task Completion**
- The system shall allow users to mark tasks as completed
- The system shall track completion timestamps
- The system shall provide visual indicators for completed tasks
- The system shall generate completion notifications

#### 3.2.3 Media Management

**FR-008: File Upload**
- The system shall support upload of image, video, and document files
- The system shall validate file types and sizes
- The system shall generate unique filenames for uploaded files
- The system shall create thumbnails for image files
- The system shall associate media files with specific tasks

**FR-009: Media Organization**
- The system shall organize media files by user and task
- The system shall provide gallery view for media files
- The system shall support media file deletion
- The system shall maintain media file metadata

**FR-010: Media Display**
- The system shall display image thumbnails in gallery view
- The system shall support video playback for uploaded videos
- The system shall provide full-size image viewing
- The system shall display file information (size, type, upload date)

#### 3.2.4 Notification System

**FR-011: Email Notifications**
- The system shall send automated email notifications for due tasks
- The system shall support multiple notification types: due today, due tomorrow, overdue
- The system shall use Brevo API for email delivery
- The system shall include task details in notification emails
- The system shall respect user notification preferences

**FR-012: In-App Notifications**
- The system shall display in-app notifications for user actions
- The system shall track notification read status
- The system shall provide notification history
- The system shall allow users to mark notifications as read

**FR-013: Notification Preferences**
- The system shall allow users to configure notification settings
- The system shall support enabling/disabling email notifications
- The system shall support enabling/disabling specific notification types
- The system shall respect user preferences when sending notifications

#### 3.2.5 Analytics and Reporting

**FR-014: Task Statistics**
- The system shall provide task completion statistics
- The system shall display total, completed, and pending task counts
- The system shall calculate completion rates
- The system shall track overdue tasks

**FR-015: Progress Tracking**
- The system shall calculate task progress based on media uploads and completion status
- The system shall provide visual progress indicators
- The system shall track task timeline and milestones

**FR-016: Media Analytics**
- The system shall track media file usage statistics
- The system shall count media files per task
- The system shall monitor storage usage

### 3.3 Non-Functional Requirements

#### 3.3.1 Performance Requirements

**NFR-001: Response Time**
- The system shall respond to user requests within 2 seconds
- The system shall load dashboard within 3 seconds
- The system shall process file uploads within 10 seconds for files up to 50MB
- The system shall generate thumbnails within 5 seconds

**NFR-002: Throughput**
- The system shall support up to 100 concurrent users
- The system shall handle up to 1000 tasks per user
- The system shall process up to 100 media files per user

**NFR-003: Scalability**
- The system shall be designed for single-server deployment
- The system shall support database growth up to 1GB
- The system shall handle file storage up to 10GB

#### 3.3.2 Security Requirements

**NFR-004: Authentication Security**
- The system shall hash passwords using secure algorithms
- The system shall implement session-based authentication
- The system shall protect against unauthorized access
- The system shall validate user permissions for all operations

**NFR-005: Data Protection**
- The system shall protect user data from unauthorized access
- The system shall validate all user inputs
- The system shall prevent SQL injection attacks
- The system shall secure file uploads and downloads

**NFR-006: Privacy**
- The system shall not share user data with third parties
- The system shall implement secure email communication
- The system shall protect user session information

#### 3.3.3 Reliability Requirements

**NFR-007: Availability**
- The system shall be available 99% of the time during business hours
- The system shall handle graceful degradation during high load
- The system shall provide error recovery mechanisms

**NFR-008: Data Integrity**
- The system shall maintain data consistency across operations
- The system shall implement proper database transactions
- The system shall prevent data corruption during file operations
- The system shall provide data backup and recovery capabilities

#### 3.3.4 Usability Requirements

**NFR-009: User Interface**
- The system shall provide an intuitive and responsive user interface
- The system shall support modern web browsers
- The system shall provide clear error messages and feedback
- The system shall implement consistent navigation patterns

**NFR-010: Accessibility**
- The system shall support keyboard navigation
- The system shall provide alternative text for images
- The system shall use sufficient color contrast
- The system shall be compatible with screen readers

#### 3.3.5 Maintainability Requirements

**NFR-011: Code Quality**
- The system shall follow Python coding standards
- The system shall include comprehensive error handling
- The system shall implement modular architecture
- The system shall provide clear documentation

**NFR-012: Extensibility**
- The system shall support easy addition of new features
- The system shall use configurable parameters
- The system shall implement plugin architecture for notifications
- The system shall support database schema evolution

---

## 4. External Interface Requirements

### 4.1 User Interfaces
Detailed specifications for each user interface component:

#### 4.1.1 Login Interface
- **URL**: `/login`
- **Method**: GET/POST
- **Input Fields**: Username, Password
- **Validation**: Required fields, credential verification
- **Response**: Success redirect to dashboard, error messages

#### 4.1.2 Registration Interface
- **URL**: `/register`
- **Method**: GET/POST
- **Input Fields**: Username, Email, Password
- **Validation**: Unique username/email, password strength
- **Response**: OTP verification required

#### 4.1.3 Dashboard Interface
- **URL**: `/dashboard`
- **Method**: GET
- **Content**: Task overview, statistics, quick actions
- **Navigation**: Links to all major features
- **Authentication**: Required

#### 4.1.4 Task Management Interface
- **URL**: `/api/tasks`
- **Method**: GET, POST, PUT, DELETE
- **Data Format**: JSON
- **Authentication**: Required
- **Features**: CRUD operations for tasks

#### 4.1.5 Media Gallery Interface
- **URL**: `/gallery`
- **Method**: GET
- **Content**: Media file grid, upload interface
- **Features**: File upload, thumbnail display, video playback

### 4.2 Hardware Interfaces
- **Server Requirements**:
  - CPU: 2+ cores
  - RAM: 4GB minimum, 8GB recommended
  - Storage: 20GB minimum, SSD recommended
  - Network: 100Mbps minimum

- **Client Requirements**:
  - Modern web browser with JavaScript enabled
  - Minimum screen resolution: 1024x768
  - Internet connection for email notifications

### 4.3 Software Interfaces
- **Operating System**: Windows 10+, macOS 10.14+, Linux (Ubuntu 18.04+)
- **Python Environment**: Python 3.7+ with pip package manager
- **Database**: SQLite 3.0+
- **Web Server**: Flask development server or production WSGI server
- **Email Service**: Brevo API integration

### 4.4 Communications Interfaces
- **HTTP/HTTPS**: RESTful API endpoints
- **SMTP**: Email delivery via Brevo API
- **File Upload**: Multipart form data
- **JSON**: Data exchange format for API responses

---

## 5. Performance Requirements

### 5.1 Response Time Requirements
- **Page Load Time**: < 3 seconds for all pages
- **API Response Time**: < 2 seconds for all API calls
- **File Upload Time**: < 10 seconds for 50MB files
- **Database Query Time**: < 1 second for standard queries
- **Email Delivery Time**: < 5 minutes for notifications

### 5.2 Throughput Requirements
- **Concurrent Users**: Support for 100 simultaneous users
- **Tasks per User**: Up to 1000 tasks per user account
- **Media Files per User**: Up to 100 media files per user
- **API Requests**: 1000 requests per minute
- **Email Notifications**: 100 emails per hour

### 5.3 Resource Utilization
- **CPU Usage**: < 80% under normal load
- **Memory Usage**: < 2GB RAM for application
- **Disk Space**: < 10GB for file storage
- **Network Bandwidth**: < 100Mbps for normal operations

### 5.4 Scalability Requirements
- **Database Growth**: Support for 1GB database size
- **File Storage**: Support for 10GB total file storage
- **User Growth**: Support for 1000 registered users
- **Task Volume**: Support for 100,000 total tasks

---

## 6. Design Constraints

### 6.1 Technical Constraints
- **Programming Language**: Python 3.7+
- **Web Framework**: Flask 3.0.3
- **Database**: SQLite (single-file database)
- **File Storage**: Local file system
- **Email Service**: Brevo API dependency
- **Deployment**: Single-server architecture

### 6.2 Business Constraints
- **Budget**: Limited to open-source technologies
- **Timeline**: Development within academic semester
- **Team Size**: Small development team
- **Maintenance**: Minimal ongoing maintenance requirements

### 6.3 Regulatory Constraints
- **Data Protection**: Compliance with basic privacy requirements
- **Security**: Implementation of secure authentication
- **Accessibility**: Basic web accessibility standards
- **Licensing**: Open-source license compliance

### 6.4 Environmental Constraints
- **Hosting**: Local or cloud hosting environment
- **Network**: Internet connectivity for email notifications
- **Storage**: Adequate disk space for file uploads
- **Backup**: Regular data backup requirements

---

## 7. Software System Attributes

### 7.1 Reliability
- **Fault Tolerance**: Graceful handling of database errors
- **Error Recovery**: Automatic recovery from common failures
- **Data Backup**: Regular backup of database and files
- **Monitoring**: Basic system health monitoring

### 7.2 Availability
- **Uptime**: 99% availability during business hours
- **Maintenance Windows**: Scheduled maintenance periods
- **Error Handling**: Comprehensive error handling and logging
- **Recovery Time**: < 30 minutes for system recovery

### 7.3 Security
- **Authentication**: Secure user authentication system
- **Authorization**: Role-based access control
- **Data Protection**: Encryption of sensitive data
- **Input Validation**: Comprehensive input validation
- **Session Management**: Secure session handling

### 7.4 Maintainability
- **Code Quality**: Clean, well-documented code
- **Modularity**: Modular architecture for easy maintenance
- **Documentation**: Comprehensive code and user documentation
- **Testing**: Unit and integration testing capabilities

### 7.5 Portability
- **Platform Independence**: Cross-platform compatibility
- **Browser Compatibility**: Support for major web browsers
- **Database Portability**: SQLite database portability
- **Configuration**: Environment-based configuration

### 7.6 Usability
- **User Interface**: Intuitive and responsive design
- **Accessibility**: Basic accessibility compliance
- **Documentation**: User-friendly documentation
- **Help System**: Context-sensitive help and error messages

---

## 8. Appendices

### 8.1 Database Schema

#### Users Table
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL
);
```

#### Tasks Table
```sql
CREATE TABLE tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    due_date DATE,
    priority TEXT DEFAULT 'medium',
    completed INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
);
```

#### Media Table
```sql
CREATE TABLE media (
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
);
```

#### Notification Tables
```sql
CREATE TABLE notification_preferences (
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
);

CREATE TABLE notification_log (
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
);

CREATE TABLE in_app_notifications (
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
);
```

### 8.2 API Endpoints

#### Authentication Endpoints
- `POST /register` - User registration
- `POST /verify-otp` - OTP verification
- `POST /login` - User login
- `GET /logout` - User logout

#### Task Management Endpoints
- `GET /api/tasks` - Get user tasks
- `POST /api/tasks` - Create new task
- `PUT /api/tasks/<id>` - Update task
- `DELETE /api/tasks/<id>` - Delete task

#### Media Management Endpoints
- `GET /api/media` - Get user media files
- `POST /api/media` - Upload media file
- `DELETE /api/media` - Delete media file
- `PUT /api/media/<id>` - Update media file

#### Notification Endpoints
- `GET /api/notifications` - Get user notifications
- `POST /api/notifications/<id>/mark-read` - Mark notification as read
- `GET /api/notification-preferences` - Get notification preferences
- `POST /api/notification-preferences` - Update notification preferences

#### Analytics Endpoints
- `GET /api/stats` - Get user statistics
- `GET /api/completed-tasks` - Get completed tasks

### 8.3 File Structure
```
Task_Scheduler_capstone_final_system_project/
├── app.py                          # Main Flask application
├── notification_system.py          # Notification system module
├── requirements.txt                # Python dependencies
├── README.md                       # Project documentation
├── app.db                          # SQLite database
├── session.json                    # Session storage
├── static/                         # Static files
│   ├── style.css                   # CSS styles
│   ├── sweetalert2@11.js           # JavaScript library
│   └── uploads/                    # Media file storage
├── templates/                      # HTML templates
│   ├── login.html                  # Login page
│   ├── register.html               # Registration page
│   ├── dashboard.html              # Dashboard page
│   ├── gallery.html                # Media gallery
│   └── ...                         # Other templates
└── venv/                          # Python virtual environment
```

### 8.4 Configuration Parameters
- **Database File**: `app.db`
- **Upload Folder**: `static/uploads`
- **Max File Size**: 50MB
- **Allowed File Types**: png, jpg, jpeg, gif, bmp, webp, mp4, avi, mov, wmv, flv, webm
- **Session Lifetime**: 7 days
- **Brevo API Key**: Environment variable configuration
- **Thumbnail Size**: 300x300 pixels

### 8.5 Error Codes and Messages
- **400**: Bad Request - Invalid input data
- **401**: Unauthorized - Authentication required
- **403**: Forbidden - Insufficient permissions
- **404**: Not Found - Resource not found
- **500**: Internal Server Error - Server-side error

### 8.6 Security Considerations
- Password hashing using Werkzeug security functions
- Session-based authentication with secure session management
- Input validation and sanitization
- File upload security with type and size validation
- SQL injection prevention using parameterized queries
- Cross-site scripting (XSS) prevention
- CSRF protection for form submissions

---

**Document End**

*This SRS document provides a comprehensive specification for the Task Scheduler System. All requirements should be reviewed and approved by stakeholders before implementation begins.* 