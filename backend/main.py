from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import sqlite3
import hashlib
import secrets

app = FastAPI(title="Python Learning Platform API")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database Setup
def get_db():
    conn = sqlite3.connect('learning_platform.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            total_points INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Courses table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            level TEXT NOT NULL,
            order_num INTEGER,
            icon TEXT
        )
    ''')
    
    # Articles table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            order_num INTEGER,
            video_url TEXT,
            FOREIGN KEY (course_id) REFERENCES courses (id)
        )
    ''')
    
    # Quizzes table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS quizzes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            article_id INTEGER,
            question TEXT NOT NULL,
            option_a TEXT NOT NULL,
            option_b TEXT NOT NULL,
            option_c TEXT NOT NULL,
            option_d TEXT NOT NULL,
            correct_answer TEXT NOT NULL,
            points INTEGER DEFAULT 10,
            FOREIGN KEY (article_id) REFERENCES articles (id)
        )
    ''')
    
    # User Progress table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            article_id INTEGER,
            completed BOOLEAN DEFAULT 0,
            score INTEGER DEFAULT 0,
            completed_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (article_id) REFERENCES articles (id),
            UNIQUE(user_id, article_id)
        )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

# ============ Pydantic Models ============
class UserRegister(BaseModel):
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class Course(BaseModel):
    id: int
    title: str
    description: str
    level: str
    order_num: int
    icon: str

class Article(BaseModel):
    id: int
    course_id: int
    title: str
    content: str
    order_num: int
    video_url: Optional[str] = None

class Quiz(BaseModel):
    id: int
    article_id: int
    question: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    points: int

class QuizSubmit(BaseModel):
    quiz_id: int
    answer: str

class ProgressUpdate(BaseModel):
    article_id: int
    completed: bool
    score: int

# ============ Helper Functions ============
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

# ============ API Routes ============

@app.get("/")
def root():
    return {"message": "Python Learning Platform API", "status": "running"}

# ========== Auth Routes ==========
@app.post("/api/register")
def register(user: UserRegister):
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        password_hash = hash_password(user.password)
        cursor.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
            (user.username, user.email, password_hash)
        )
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        
        return {
            "message": "User registered successfully",
            "user": {"id": user_id, "username": user.username, "email": user.email}
        }
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="Username or email already exists")

@app.post("/api/login")
def login(credentials: UserLogin):
    conn = get_db()
    cursor = conn.cursor()
    
    password_hash = hash_password(credentials.password)
    cursor.execute(
        "SELECT id, username, email, total_points FROM users WHERE username = ? AND password_hash = ?",
        (credentials.username, password_hash)
    )
    user = cursor.fetchone()
    conn.close()
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    return {
        "message": "Login successful",
        "user": {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "total_points": user["total_points"]
        }
    }

# ========== Course Routes ==========
@app.get("/api/courses")
def get_courses(level: Optional[str] = None):
    conn = get_db()
    cursor = conn.cursor()
    
    if level:
        cursor.execute("SELECT * FROM courses WHERE level = ? ORDER BY order_num", (level,))
    else:
        cursor.execute("SELECT * FROM courses ORDER BY level, order_num")
    
    courses = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return courses

@app.get("/api/courses/{course_id}")
def get_course(course_id: int):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM courses WHERE id = ?", (course_id,))
    course = cursor.fetchone()
    
    if not course:
        conn.close()
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Get articles for this course
    cursor.execute("SELECT * FROM articles WHERE course_id = ? ORDER BY order_num", (course_id,))
    articles = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    result = dict(course)
    result["articles"] = articles
    return result

# ========== Article Routes ==========
@app.get("/api/articles/{article_id}")
def get_article(article_id: int):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM articles WHERE id = ?", (article_id,))
    article = cursor.fetchone()
    
    if not article:
        conn.close()
        raise HTTPException(status_code=404, detail="Article not found")
    
    # Get quizzes for this article
    cursor.execute(
        "SELECT id, article_id, question, option_a, option_b, option_c, option_d, points FROM quizzes WHERE article_id = ?",
        (article_id,)
    )
    quizzes = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    result = dict(article)
    result["quizzes"] = quizzes
    return result

# ========== Quiz Routes ==========
@app.post("/api/quiz/submit")
def submit_quiz(user_id: int, submission: QuizSubmit):
    conn = get_db()
    cursor = conn.cursor()
    
    # Get the correct answer
    cursor.execute("SELECT correct_answer, points, article_id FROM quizzes WHERE id = ?", (submission.quiz_id,))
    quiz = cursor.fetchone()
    
    if not quiz:
        conn.close()
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    is_correct = submission.answer.upper() == quiz["correct_answer"].upper()
    points_earned = quiz["points"] if is_correct else 0
    
    # Update user points
    if is_correct:
        cursor.execute("UPDATE users SET total_points = total_points + ? WHERE id = ?", (points_earned, user_id))
    
    conn.commit()
    conn.close()
    
    return {
        "correct": is_correct,
        "points_earned": points_earned,
        "correct_answer": quiz["correct_answer"] if not is_correct else None
    }

# ========== Progress Routes ==========
@app.post("/api/progress")
def update_progress(user_id: int, progress: ProgressUpdate):
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO user_progress (user_id, article_id, completed, score, completed_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id, article_id) 
            DO UPDATE SET completed = ?, score = ?, completed_at = CURRENT_TIMESTAMP
        """, (user_id, progress.article_id, progress.completed, progress.score, 
              progress.completed, progress.score))
        
        conn.commit()
        conn.close()
        return {"message": "Progress updated successfully"}
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/progress/{user_id}")
def get_progress(user_id: int):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT up.*, a.title as article_title, c.title as course_title
        FROM user_progress up
        JOIN articles a ON up.article_id = a.id
        JOIN courses c ON a.course_id = c.id
        WHERE up.user_id = ?
        ORDER BY up.completed_at DESC
    """, (user_id,))
    
    progress = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return progress

@app.get("/api/stats/{user_id}")
def get_stats(user_id: int):
    conn = get_db()
    cursor = conn.cursor()
    
    # Get user info
    cursor.execute("SELECT username, total_points FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    
    if not user:
        conn.close()
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get completed articles count
    cursor.execute("SELECT COUNT(*) as completed FROM user_progress WHERE user_id = ? AND completed = 1", (user_id,))
    completed = cursor.fetchone()["completed"]
    
    # Get total articles count
    cursor.execute("SELECT COUNT(*) as total FROM articles")
    total = cursor.fetchone()["total"]
    
    # Get recent activities
    cursor.execute("""
        SELECT a.title, up.score, up.completed_at
        FROM user_progress up
        JOIN articles a ON up.article_id = a.id
        WHERE up.user_id = ?
        ORDER BY up.completed_at DESC
        LIMIT 5
    """, (user_id,))
    recent_activities = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    return {
        "username": user["username"],
        "total_points": user["total_points"],
        "completed_articles": completed,
        "total_articles": total,
        "completion_rate": round((completed / total * 100), 1) if total > 0 else 0,
        "recent_activities": recent_activities
    }

# ========== Seed Data Route (for development) ==========
@app.post("/api/seed-data")
def seed_data():
    conn = get_db()
    cursor = conn.cursor()
    
    # Check if data already exists
    cursor.execute("SELECT COUNT(*) as count FROM courses")
    if cursor.fetchone()["count"] > 0:
        conn.close()
        return {"message": "Data already exists"}
    
    # Insert sample courses
    courses = [
        ("Python Basics", "Learn the fundamentals of Python programming", "beginner", 1, "📚"),
        ("Data Types & Variables", "Master Python data types and variables", "beginner", 2, "🔢"),
        ("Control Flow", "Understand loops and conditionals", "intermediate", 3, "🔄"),
        ("Functions", "Write reusable code with functions", "intermediate", 4, "⚡"),
        ("OOP Concepts", "Object-Oriented Programming in Python", "advanced", 5, "🎯"),
    ]
    
    cursor.executemany(
        "INSERT INTO courses (title, description, level, order_num, icon) VALUES (?, ?, ?, ?, ?)",
        courses
    )
    
    # Insert sample articles
    articles = [
        (1, "Introduction to Python", """
# Welcome to Python!

Python is a high-level, interpreted programming language known for its simplicity and readability.

## Why Learn Python?
- Easy to learn and use
- Versatile (web, data science, AI, automation)
- Large community and libraries
- High demand in job market

## Your First Python Program
```python
print("Hello, World!")
```

This simple line prints text to the console. Welcome to Python programming!
        """, 1, "https://www.youtube.com/embed/nLRL_NcnK-4"),
        
        (1, "Installing Python", """
# Setting Up Python

Let's get Python installed on your computer!

## Installation Steps
1. Visit python.org
2. Download Python 3.x
3. Run the installer
4. Check 'Add Python to PATH'
5. Verify installation

## Verify Installation
```python
python --version
```

You should see Python 3.x.x displayed!
        """, 2, None),
        
        (2, "Variables in Python", """
# Understanding Variables

Variables are containers for storing data values.

## Creating Variables
```python
name = "Alice"
age = 25
height = 5.6
is_student = True
```

## Variable Rules
- Start with letter or underscore
- Can contain letters, numbers, underscores
- Case-sensitive (age ≠ Age)
- Cannot use Python keywords

Try creating your own variables!
        """, 1, None),
    ]
    
    cursor.executemany(
        "INSERT INTO articles (course_id, title, content, order_num, video_url) VALUES (?, ?, ?, ?, ?)",
        articles
    )
    
    # Insert sample quizzes
    quizzes = [
        (1, "What does print() do in Python?", "Saves data to file", "Displays output to console", "Creates a variable", "Imports a module", "B", 10),
        (1, "Is Python a compiled or interpreted language?", "Compiled", "Interpreted", "Both", "Neither", "B", 10),
        (3, "Which is a valid variable name?", "2name", "my-var", "my_var", "my var", "C", 10),
        (3, "What will this print: x = 5; print(x)?", "x", "5", "'5'", "Error", "B", 10),
    ]
    
    cursor.executemany(
        "INSERT INTO quizzes (article_id, question, option_a, option_b, option_c, option_d, correct_answer, points) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        quizzes
    )
    
    conn.commit()
    conn.close()
    
    return {"message": "Sample data inserted successfully!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)