# Task Scheduler Flask App

A simple task scheduler system built with Flask, supporting user login, persistent JSON storage, and task management with priority and reminders.

## Features
- User login with persistent data (stored in `users.json`)
- Add, edit, and delete tasks (title, priority, due date)
- Display tasks sorted by priority and due date
- All tasks saved in `tasks.json`
- API endpoint for tasks at `/api/tasks`

## Setup Instructions
1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
2. **Run the app:**
   ```bash
   python app.py
   ```
3. **Access the app:**
   Open [http://127.0.0.1:5000/](http://127.0.0.1:5000/) in your browser.
   - Default login: `admin` / `admin`

## Developer Notes
- User authentication is basic; for production, improve password security (hashing, user registration, etc.).
- Tasks are stored in a JSON file for simplicity; consider a database for scaling.
- Reminders and notifications can be added in future iterations.
- HTML templates (`login.html`, `index.html`, `add_task.html`, `edit_task.html`) are required for full functionality.
- For collaboration, see comments in `app.py` and templates. 