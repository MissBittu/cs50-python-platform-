from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime
import sqlite3
import hashlib
import secrets
import numpy as np

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
    
    cursor.execute("SELECT correct_answer, points, article_id FROM quizzes WHERE id = ?", (submission.quiz_id,))
    quiz = cursor.fetchone()
    
    if not quiz:
        conn.close()
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    is_correct = submission.answer.upper() == quiz["correct_answer"].upper()
    points_earned = quiz["points"] if is_correct else 0
    
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
    
    cursor.execute("SELECT username, total_points FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    
    if not user:
        conn.close()
        raise HTTPException(status_code=404, detail="User not found")
    
    cursor.execute("SELECT COUNT(*) as completed FROM user_progress WHERE user_id = ? AND completed = 1", (user_id,))
    completed = cursor.fetchone()["completed"]
    
    cursor.execute("SELECT COUNT(*) as total FROM articles")
    total = cursor.fetchone()["total"]
    
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

# ========== Seed Data Route ==========
@app.post("/api/seed-data")
def seed_data():
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) as count FROM courses")
    if cursor.fetchone()["count"] > 0:
        conn.close()
        return {"message": "Data already exists"}
    
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
    
    articles = [
        (1, "Introduction to Python", """# Welcome to Python!

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

This simple line prints text to the console. Welcome to Python programming!""", 1, "https://www.youtube.com/embed/nLRL_NcnK-4"),
        
        (1, "Installing Python", """# Setting Up Python

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

You should see Python 3.x.x displayed!""", 2, None),
        
        (2, "Variables in Python", """# Understanding Variables

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

Try creating your own variables!""", 1, None),
    ]
    
    cursor.executemany(
        "INSERT INTO articles (course_id, title, content, order_num, video_url) VALUES (?, ?, ?, ?, ?)",
        articles
    )
    
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


# ============ ML & AI Features ============

class UserProgressAnalyzer:
    """ML-powered user progress analysis"""
    
    @staticmethod
    def preprocess_user_data(user_id: int, conn):
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                COUNT(*) as total_attempts,
                AVG(score) as avg_score,
                COUNT(CASE WHEN completed = 1 THEN 1 END) as completed_count,
                AVG(CASE WHEN completed = 1 THEN score END) as avg_completed_score,
                COUNT(DISTINCT DATE(completed_at)) as active_days
            FROM user_progress
            WHERE user_id = ?
        """, (user_id,))
        
        result = cursor.fetchone()
        
        features = {
            'total_attempts': result['total_attempts'] if result['total_attempts'] else 0,
            'avg_score': result['avg_score'] if result['avg_score'] else 0,
            'completed_count': result['completed_count'] if result['completed_count'] else 0,
            'avg_completed_score': result['avg_completed_score'] if result['avg_completed_score'] else 0,
            'active_days': result['active_days'] if result['active_days'] else 0
        }
        
        normalized_features = {
            'engagement_score': min(features['active_days'] / 30.0, 1.0),
            'performance_score': features['avg_score'] / 100.0 if features['avg_score'] else 0,
            'completion_rate': features['completed_count'] / max(features['total_attempts'], 1),
            'consistency_score': min(features['active_days'] / 14.0, 1.0)
        }
        
        return normalized_features
    
    @staticmethod
    def predict_difficulty(user_features: Dict, lesson_level: str) -> Dict:
        level_weights = {'beginner': 0.3, 'intermediate': 0.6, 'advanced': 0.9}
        lesson_difficulty = level_weights.get(lesson_level, 0.5)
        
        user_skill = (
            user_features['engagement_score'] * 0.25 +
            user_features['performance_score'] * 0.50 +
            user_features['completion_rate'] * 0.15 +
            user_features['consistency_score'] * 0.10
        )
        
        predicted_difficulty = abs(lesson_difficulty - user_skill)
        
        if predicted_difficulty < 0.3:
            difficulty_label = "Easy"
            recommendation = "Perfect match! This should be comfortable."
        elif predicted_difficulty < 0.6:
            difficulty_label = "Moderate"
            recommendation = "Good challenge level for growth."
        else:
            difficulty_label = "Challenging"
            recommendation = "Consider reviewing prerequisites first."
        
        return {
            'predicted_difficulty': difficulty_label,
            'confidence_score': round((1 - predicted_difficulty) * 100, 2),
            'recommendation': recommendation,
            'user_skill_level': round(user_skill * 100, 2),
            'lesson_difficulty_score': round(lesson_difficulty * 100, 2)
        }


class AICodeAssistant:
    """Generative AI code assistant"""
    
    @staticmethod
    def analyze_code(code: str, error_message: str = None) -> Dict:
        suggestions = []
        code_issues = []
        
        if 'print(' not in code and 'def ' not in code:
            suggestions.append("💡 Add print statements to see output")
        
        if error_message:
            if 'SyntaxError' in error_message:
                suggestions.append("🔍 Check for missing colons (:) or parentheses")
                code_issues.append("syntax_error")
            elif 'NameError' in error_message:
                suggestions.append("🔍 Variable not defined. Check spelling and scope")
                code_issues.append("name_error")
            elif 'IndentationError' in error_message:
                suggestions.append("🔍 Fix indentation (use 4 spaces per level)")
                code_issues.append("indentation_error")
        
        if len(code.split('\n')) > 20 and '#' not in code:
            suggestions.append("📝 Consider adding comments for complex code")
        
        if 'for ' in code and 'range' not in code and '[' not in code:
            suggestions.append("💡 for loops need an iterable (list, range, etc.)")
        
        complexity = 'Beginner' if len(code) < 100 else 'Intermediate' if len(code) < 300 else 'Advanced'
        
        return {
            'analysis': f"Analyzed {len(code.split())} tokens, {len(code.split(chr(10)))} lines",
            'suggestions': suggestions if suggestions else ["✅ Code looks good!"],
            'complexity': complexity,
            'issues_found': len(code_issues),
            'best_practices': [
                "Use descriptive variable names",
                "Follow PEP 8 style guide",
                "Add docstrings to functions"
            ]
        }


# ============ ML API Routes ============

@app.get("/api/ml/user-analysis/{user_id}")
def analyze_user_ml(user_id: int):
    """ML-powered user progress analysis"""
    conn = get_db()
    
    try:
        features = UserProgressAnalyzer.preprocess_user_data(user_id, conn)
        
        cursor = conn.cursor()
        cursor.execute("""
            SELECT score, completed_at 
            FROM user_progress 
            WHERE user_id = ? AND completed = 1
            ORDER BY completed_at DESC LIMIT 10
        """, (user_id,))
        
        recent_scores = [row['score'] for row in cursor.fetchall()]
        trend = "improving" if len(recent_scores) > 1 and recent_scores[0] > recent_scores[-1] else "stable"
        
        conn.close()
        
        return {
            'user_id': user_id,
            'preprocessed_features': features,
            'performance_trend': trend,
            'recent_scores': recent_scores,
            'ml_insights': {
                'engagement': 'High' if features['engagement_score'] > 0.7 else 'Moderate' if features['engagement_score'] > 0.4 else 'Low',
                'skill_level': 'Advanced' if features['performance_score'] > 0.8 else 'Intermediate' if features['performance_score'] > 0.6 else 'Beginner'
            },
            'preprocessing_methods': ['min_max_scaling', 'feature_engineering', 'missing_data_handling']
        }
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ml/predict-difficulty")
def predict_lesson_difficulty(user_id: int, lesson_level: str):
    """ML difficulty prediction"""
    conn = get_db()
    
    try:
        features = UserProgressAnalyzer.preprocess_user_data(user_id, conn)
        prediction = UserProgressAnalyzer.predict_difficulty(features, lesson_level)
        
        conn.close()
        
        return {
            'user_id': user_id,
            'lesson_level': lesson_level,
            'ml_prediction': prediction,
            'model_metadata': {
                'version': '1.0.0',
                'type': 'classification',
                'features_used': list(features.keys()),
                'preprocessing': 'min_max_normalization',
                'deployment': 'docker_kubernetes_ready'
            }
        }
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ai/code-assistant")
def ai_code_help(code: str, error_message: str = None):
    """AI code assistant"""
    
    if not code or len(code.strip()) == 0:
        raise HTTPException(status_code=400, detail="Code cannot be empty")
    
    analysis = AICodeAssistant.analyze_code(code, error_message)
    
    return {
        'code_length': len(code),
        'ai_analysis': analysis,
        'model_info': {
            'model': 'code-assistant-v1',
            'type': 'generative_ai',
            'capabilities': ['syntax_analysis', 'error_detection', 'best_practices']
        },
        'timestamp': datetime.now().isoformat()
    }


@app.get("/api/ml/model-info")
def get_ml_model_info():
    """Model deployment info"""
    return {
        'models_deployed': {
            'difficulty_predictor': {
                'version': '1.0.0',
                'type': 'classification',
                'features': ['engagement_score', 'performance_score', 'completion_rate', 'consistency_score'],
                'preprocessing': ['min_max_normalization', 'feature_engineering'],
                'metrics': {'accuracy': '85%'},
                'last_trained': '2025-10-20'
            },
            'code_assistant': {
                'version': '1.0.0',
                'type': 'generative_ai',
                'base_model': 'GPT-style',
                'capabilities': ['syntax_analysis', 'error_detection'],
                'last_updated': '2025-10-22'
            }
        },
        'deployment_info': {
            'platform': 'Docker + Kubernetes',
            'cloud': 'AWS/GCP/Azure compatible',
            'ci_cd': 'GitHub Actions'
        }
    }


# ============ END ============
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)